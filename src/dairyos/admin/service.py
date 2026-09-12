"""Application service for privileged DairyOS lifecycle administration."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dairyos.data.database.backup import verify_backup_artifact
from dairyos.lifecycle.manager import LifecycleError, LifecycleManager, UninstallMode
from dairyos.lifecycle.purge import create_external_purge_backup, purge_data_after_backup
from dairyos.lifecycle.reset import (
    reset_operational_data,
    verify_file_projection_zero_state,
    verify_zero_state,
)
from dairyos.lifecycle.restore import restore_snapshot

RESET_CONFIRMATION = "RESET DAIRYOS DATA"
PURGE_CONFIRMATION = "PURGE DAIRYOS DATA"
CLEAN_INSTALL_CONFIRMATION = "CLEAN INSTALL DAIRYOS DATA"


@dataclass(frozen=True)
class AdminResult:
    operation: str
    success: bool
    message: str
    artifact: str | None = None


class AdminService:
    """Administrative facade over the canonical lifecycle boundary."""

    def __init__(self, manager: LifecycleManager):
        self.manager = manager

    def status(self) -> dict[str, object]:
        return self.manager.validate(require_database=bool(self.manager.database_url))

    def backup(self, label: str = "admin") -> AdminResult:
        if not self.manager.database_url:
            raise LifecycleError(
                "Admin backup requires the canonical PostgreSQL database authority."
            )
        artifact = self.manager.backup(label=label, require_database=True)
        _record_database_checksum(artifact)
        _verify_backup_directory(artifact, require_database=True)
        return AdminResult("backup", True, "Backup completed and verified.", str(artifact))

    def restore(self, backup: str | Path) -> AdminResult:
        if not self.manager.database_url:
            raise LifecycleError(
                "Admin restore requires the canonical PostgreSQL database authority."
            )
        from dairyos.admin.backup_catalog import verify_restore_candidate
        from dairyos.admin.database_restore import restore_database_only

        candidate = verify_restore_candidate(backup)
        _assert_runtime_stopped()
        if candidate.kind == "database":
            restore_database_only(self.manager, candidate.path)
            return AdminResult("restore", True, "Database restored and validated. Operational read models rebuilt; other files and local Admin settings were retained.", str(candidate.path))
        _verify_backup_directory(candidate.path, require_database=True)
        restore_snapshot(self.manager, candidate.path)
        self.manager.validate(require_database=bool(self.manager.database_url))
        return AdminResult("restore", True, "Snapshot restored and validated.", str(Path(backup).resolve()))

    def rollback(self, backup: str | Path) -> AdminResult:
        from dairyos.admin.backup_catalog import verify_restore_candidate

        verify_restore_candidate(backup)
        if Path(backup).is_file():
            result = self.restore(backup)
            return AdminResult("rollback", result.success, result.message, result.artifact)
        _assert_runtime_stopped()
        _verify_backup_directory(backup)
        result = self.manager.rollback(backup)
        return AdminResult(
            "rollback",
            bool(result.get("valid")),
            "Rollback completed and validated.",
            str(Path(backup).resolve()),
        )

    def reset(
        self,
        confirmation: str,
        backup_before_reset: bool = True,
        reset_context: dict[str, object] | None = None,
    ) -> AdminResult:
        """Reset operational state through a verified external recovery point."""
        if confirmation != RESET_CONFIRMATION:
            raise LifecycleError(
                f"Reset requires the exact confirmation token: {RESET_CONFIRMATION!r}"
            )
        if not self.manager.database_url:
            raise LifecycleError("Reset requires DAIRYOS_DATABASE_URL to be configured.")

        _admin_stage("reset: lifecycle validation")
        self.manager.validate(require_database=True)

        context = _reset_context(self.manager, reset_context, confirmation)
        _admin_stage("reset: pre-reset backup")
        artifact = (
            self.manager.backup(label="pre-reset", require_database=True)
            if backup_before_reset
            else None
        )
        if artifact is None:
            raise LifecycleError("Reset requires a verified pre-reset backup.")

        _admin_stage(f"reset: backup complete: {artifact}")
        _admin_stage("reset: recording database checksum")
        _record_database_checksum(artifact)
        _write_reset_manifest(artifact, context)
        _write_runtime_reset_audit(
            getattr(self.manager, "data_root", None),
            {"event": "reset-intent", **context, "artifact": str(artifact)},
        )

        _admin_stage("reset: runtime stopped check")
        _assert_runtime_stopped()
        _admin_stage("reset: copying external recovery artifact")
        recovery_artifact = _copy_external_recovery_artifact(artifact)
        _admin_stage(f"reset: external recovery copy complete: {recovery_artifact}")
        _admin_stage("reset: verifying recovery artifact")
        _verify_backup_directory(recovery_artifact)
        _admin_stage("reset: recording reset intent")
        _write_audit_event(recovery_artifact, "reset-intent", context)
        try:
            _admin_stage("reset: destructive SQL transaction starting")
            execution = reset_operational_data(
                self.manager.database_url,
                updated_by="DairyOS Admin Tool",
                data_root=getattr(self.manager, "data_root", None),
            )
            _admin_stage("reset: destructive SQL transaction complete")
            remaining = verify_zero_state(self.manager.database_url)
            data_root = getattr(self.manager, "data_root", None)
            if data_root is not None:
                remaining.update(verify_file_projection_zero_state(data_root))
            if remaining:
                raise LifecycleError(
                    "Reset completed but zero-state verification failed: "
                    + ", ".join(
                        f"{table}={count}" for table, count in sorted(remaining.items())
                    )
                )
            _admin_stage("reset: zero-state verification complete")
            _write_audit_event(
                recovery_artifact,
                "reset-result",
                {
                    **context,
                    "status": "success",
                    "completed_at": _utc_now(),
                    "completed_at_local": _local_now(),
                    "tables_cleared": list(execution.tables_cleared),
                },
            )
            _write_runtime_reset_audit(
                getattr(self.manager, "data_root", None),
                {
                    "event": "reset-result",
                    **context,
                    "status": "success",
                    "completed_at": _utc_now(),
                    "completed_at_local": _local_now(),
                    "tables_cleared": list(execution.tables_cleared),
                },
            )
            _admin_stage("reset: successful")
            return AdminResult(
                "reset",
                True,
                "Operational data reset, deployment deactivated, and zero-state verified.",
                str(recovery_artifact),
            )
        except Exception as exc:
            _admin_stage(f"reset: mutation failed: {exc}")
            _write_audit_event(
                recovery_artifact,
                "reset-result",
                {
                    **context,
                    "status": "failed",
                    "completed_at": _utc_now(),
                    "completed_at_local": _local_now(),
                    "error": str(exc),
                },
            )
            _write_runtime_reset_audit(
                getattr(self.manager, "data_root", None),
                {
                    "event": "reset-result",
                    **context,
                    "status": "failed",
                    "completed_at": _utc_now(),
                    "completed_at_local": _local_now(),
                    "error": str(exc),
                },
            )
            try:
                _admin_stage("reset: automatic rollback starting")
                self.manager.rollback(artifact)
                _admin_stage("reset: automatic rollback complete")
            except Exception as rollback_exc:
                _admin_stage(f"reset: automatic rollback failed: {rollback_exc}")
                raise LifecycleError(
                    f"Reset failed and automatic recovery also failed: {rollback_exc}"
                ) from exc
            raise LifecycleError(f"Reset failed; pre-reset state was restored: {exc}") from exc

    def clean_install(
        self,
        confirmation: str,
        *,
        requested_by: str = "DairyOS Installer",
        requested_at: str | None = None,
    ) -> AdminResult:
        """Create a recovery copy, then leave the active farm completely empty.

        A clean installation is intentionally different from an ordinary
        operational reset.  The active ``storage``, ``logs`` and ``backups``
        trees are emptied after the authoritative database reset, while a
        verified recovery copy remains outside the active data root.  Private
        PostgreSQL and local security/lifecycle metadata are retained because
        they are runtime infrastructure, not farm records.
        """
        if confirmation != CLEAN_INSTALL_CONFIRMATION:
            raise LifecycleError(
                "Clean installation requires the exact confirmation token: "
                f"{CLEAN_INSTALL_CONFIRMATION!r}"
            )
        if not self.manager.database_url:
            raise LifecycleError(
                "Clean installation requires the canonical PostgreSQL database authority."
            )

        _admin_stage("clean-install: lifecycle validation")
        self.manager.validate(require_database=True)
        context = {
            "reset_operation": "CLEAN_INSTALL",
            "requested_by": str(requested_by or "DairyOS Installer").strip(),
            "requested_at": str(requested_at or _utc_now()),
            "confirmation": confirmation,
        }
        artifact: Path | None = None
        recovery_artifact: Path | None = None
        try:
            _admin_stage("clean-install: pre-clean backup")
            artifact = self.manager.backup(
                label="pre-clean-install",
                require_database=True,
            )
            _record_database_checksum(artifact)
            _write_reset_manifest(artifact, context)
            recovery_artifact = _copy_external_recovery_artifact(artifact)
            _verify_backup_directory(recovery_artifact, require_database=True)
            _write_audit_event(recovery_artifact, "clean-install-intent", context)

            _assert_runtime_stopped()
            _admin_stage("clean-install: authoritative reset")
            execution = reset_operational_data(
                self.manager.database_url,
                updated_by="DairyOS Installer",
                data_root=getattr(self.manager, "data_root", None),
            )
            remaining = verify_zero_state(self.manager.database_url)
            data_root = getattr(self.manager, "data_root", None)
            if data_root is not None:
                remaining.update(verify_file_projection_zero_state(data_root))
            if remaining:
                raise LifecycleError(
                    "Clean installation reset did not reach zero state: "
                    + ", ".join(
                        f"{table}={count}" for table, count in sorted(remaining.items())
                    )
                )

            if data_root is None:
                raise LifecycleError("Clean installation has no managed data root.")
            _clear_active_clean_state(data_root, protected_backup=artifact)
            _clear_clean_lifecycle_backup_pointer(data_root)
            residual = _verify_active_clean_state(
                data_root,
                allowed_backup=artifact,
            )
            if residual:
                raise LifecycleError(
                    "Clean installation left active farm material: "
                    + ", ".join(residual)
                )
            _remove_path(artifact)
            residual = _verify_active_clean_state(data_root)
            if residual:
                raise LifecycleError(
                    "Clean installation could not clear its final recovery artifact: "
                    + ", ".join(residual)
                )

            _write_audit_event(
                recovery_artifact,
                "clean-install-result",
                {
                    **context,
                    "status": "success",
                    "completed_at": _utc_now(),
                    "tables_cleared": list(execution.tables_cleared),
                    "active_logs_cleared": True,
                    "active_backups_cleared": True,
                },
            )
            _admin_stage("clean-install: successful")
            return AdminResult(
                "clean-install",
                True,
                "Clean installation completed; active farm data and visible logs are empty. "
                "A verified recovery copy was retained outside the active data root.",
                str(recovery_artifact),
            )
        except Exception as exc:
            if recovery_artifact is not None:
                try:
                    _write_audit_event(
                        recovery_artifact,
                        "clean-install-result",
                        {
                            **context,
                            "status": "failed",
                            "completed_at": _utc_now(),
                            "error": str(exc),
                        },
                    )
                except Exception as audit_exc:  # pragma: no cover - filesystem-specific
                    # A failed diagnostic write must never prevent recovery.
                    _admin_stage(
                        f"clean-install: failure audit could not be written: {audit_exc}"
                    )

            # The active artifact is removed only after the zero-state checks,
            # but a late filesystem/audit failure can occur after that point.
            # The verified external copy is therefore the durable fallback.
            rollback_source = next(
                (
                    candidate
                    for candidate in (recovery_artifact, artifact)
                    if candidate is not None and candidate.exists()
                ),
                None,
            )
            if rollback_source is not None:
                try:
                    _admin_stage("clean-install: automatic rollback")
                    self.manager.rollback(rollback_source)
                except Exception as rollback_exc:
                    raise LifecycleError(
                        "Clean installation failed and automatic recovery also failed: "
                        f"{rollback_exc}"
                    ) from exc
            else:
                raise LifecycleError(
                    "Clean installation failed and no verified recovery artifact remained: "
                    f"{exc}"
                ) from exc
            raise LifecycleError(
                f"Clean installation failed; pre-clean state was restored: {exc}"
            ) from exc

    def purge(self, confirmation: str) -> AdminResult:
        if confirmation != PURGE_CONFIRMATION:
            raise LifecycleError(
                f"Permanent purge requires the exact confirmation token: {PURGE_CONFIRMATION!r}"
            )
        artifact = create_external_purge_backup(self.manager)
        purge_data_after_backup(self.manager, create_backup=False)
        return AdminResult("purge", True, "Data root purged after external backup.", str(artifact))

    def uninstall(self, purge: bool = False, confirmation: str | None = None) -> AdminResult:
        mode = UninstallMode.PURGE_DATA if purge else UninstallMode.KEEP_DATA
        self.manager.uninstall(mode=mode, confirmation=confirmation)
        return AdminResult("uninstall", True, "Uninstall completed.")


def _admin_stage(message: str) -> None:
    print(f"[ADMIN-RESET] {message}", file=sys.stderr, flush=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _local_now() -> str:
    """Return the Windows host local timestamp for operator-readable audit data."""
    return datetime.now().astimezone().isoformat()


def _reset_context(
    manager: LifecycleManager,
    supplied: dict[str, object] | None,
    confirmation: str,
) -> dict[str, object]:
    supplied_was_omitted = supplied is None
    supplied = supplied or {}
    farm_name = str(supplied.get("farm_name") or "").strip()
    if not farm_name:
        if supplied_was_omitted:
            # The in-application Settings path always supplies the
            # authoritative farm name captured before the reset request is
            # queued.  Keep the internal compatibility facade usable by
            # isolated lifecycle callers without making a hidden database
            # connection in their unit tests.
            farm_name = str(getattr(manager, "farm_name", "DairyOS farm")).strip()
        else:
            farm_name = _read_farm_name(manager)
    if not farm_name:
        raise LifecycleError(
            "Reset cannot proceed because the complete farm name could not be recorded."
        )
    requested_at_utc = str(
        supplied.get("requested_at_utc")
        or supplied.get("requested_at")
        or _utc_now()
    )
    requested_at_local = str(
        supplied.get("requested_at_local")
        or _local_now()
    )
    requested_by = str(supplied.get("requested_by") or "Settings Operator")
    execution_started_at_utc = _utc_now()
    execution_started_at_local = _local_now()
    context = {
        "reset_operation": "ZERO_STATE_RESET",
        "farm_name": farm_name,
        "requested_by": requested_by,
        # Keep requested_at/execution_started_at as UTC compatibility fields;
        # the explicit suffixes make the audit representation unambiguous.
        "requested_at": requested_at_utc,
        "requested_at_utc": requested_at_utc,
        "requested_at_local": requested_at_local,
        "execution_started_at": execution_started_at_utc,
        "execution_started_at_utc": execution_started_at_utc,
        "execution_started_at_local": execution_started_at_local,
        "confirmation": confirmation,
    }
    request_confirmation = str(supplied.get("request_confirmation") or "").strip()
    if request_confirmation:
        context["request_confirmation"] = request_confirmation
    return context


def _read_farm_name(manager: LifecycleManager) -> str:
    database_url = getattr(manager, "database_url", None)
    if not database_url:
        return ""
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(database_url)
        try:
            with engine.connect() as connection:
                value = connection.execute(
                    text("SELECT value FROM app_settings WHERE key = 'farm_name'")
                ).scalar()
        finally:
            engine.dispose()
        return str(value or "").strip()
    except Exception as exc:
        raise LifecycleError(
            "Reset cannot read the farm name from the authoritative settings record."
        ) from exc


def _write_reset_manifest(artifact: str | Path, context: dict[str, object]) -> None:
    manifest_path = Path(artifact).resolve() / "backup.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("backup manifest is not an object")
        manifest["reset"] = {**context, "status": "REQUESTED"}
        temporary = manifest_path.with_name(f".{manifest_path.name}.reset-tmp")
        temporary.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, manifest_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LifecycleError(
            "Reset cannot save the farm name and reset date/time into the verified recovery manifest."
        ) from exc


def _write_runtime_reset_audit(
    data_root: str | Path | None,
    record: dict[str, object],
) -> None:
    if data_root is None:
        return
    root = Path(data_root).expanduser().resolve()
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "system-reset-audit.jsonl"
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def _assert_runtime_stopped() -> None:
    """Fail closed when the normal DairyOS backend is still listening."""
    host = os.environ.get("DAIRYOS_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("DAIRYOS_PORT", "8000"))
    except ValueError as exc:
        raise LifecycleError("DAIRYOS_PORT must be an integer for administrative reset.") from exc
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        try:
            sock.connect((host, port))
        except OSError:
            return
    raise LifecycleError(
        f"DairyOS runtime is still listening on {host}:{port}. Stop the operational application before reset or recovery."
    )


def _record_database_checksum(backup: str | Path) -> None:
    path = Path(backup).resolve()
    manifest_path = path / "backup.json"
    if not manifest_path.is_file():
        raise LifecycleError(f"Backup manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database_backup = manifest.get("database_backup")
    if not database_backup:
        return
    metadata = verify_backup_artifact(path / str(database_backup))
    manifest["database_backup_sha256"] = metadata["sha256"]
    manifest["database_backup_size_bytes"] = metadata["size_bytes"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_backup_directory(
    backup: str | Path,
    *,
    require_database: bool = True,
) -> None:
    path = Path(backup).resolve()
    manifest_path = path / "backup.json"
    if not manifest_path.is_file():
        raise LifecycleError(f"Invalid DairyOS backup: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database_backup = manifest.get("database_backup")
    if require_database and not database_backup:
        raise LifecycleError(
            "Verified DairyOS backup is missing its PostgreSQL database dump."
        )
    if database_backup:
        if require_database and manifest.get("database_backup_archive_verified") is not True:
            raise LifecycleError(
                "PostgreSQL backup archive was not verified when the backup was created."
            )
        dump_path = path / str(database_backup)
        metadata = verify_backup_artifact(dump_path)
        expected = manifest.get("database_backup_sha256")
        if expected and str(metadata["sha256"]).lower() != str(expected).lower():
            raise LifecycleError("PostgreSQL backup SHA-256 verification failed.")
    files_root = path / "files"
    for entry in manifest.get("files", []):
        relative = Path(str(entry["path"]))
        source = files_root / relative
        if not source.is_file():
            raise LifecycleError(f"Backup file is missing: {relative}")
        expected = str(entry.get("sha256", ""))
        if expected and _sha256(source) != expected:
            raise LifecycleError(f"Backup file SHA-256 verification failed: {relative}")


def _copy_external_recovery_artifact(backup: Path) -> Path:
    configured = os.environ.get("DAIRYOS_RECOVERY_ROOT")
    root = Path(configured).expanduser().resolve() if configured else backup.parents[2] / "recovery"
    active_root = backup.parent.parent.resolve()
    try:
        root.relative_to(active_root)
    except ValueError:
        pass
    else:
        raise LifecycleError(
            "DairyOS recovery storage must be outside the active farm data root."
        )
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{backup.name}-external"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(backup, destination)
    return destination


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _clear_active_clean_state(
    data_root: str | Path,
    *,
    protected_backup: str | Path,
) -> None:
    """Remove active farm files while preserving runtime infrastructure."""
    root = Path(data_root).expanduser().resolve()
    protected = Path(protected_backup).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    # The database has already been cleared transactionally.  Storage and logs
    # are projections/diagnostics and must not make a clean install look like a
    # continuation of the old farm.
    for name in ("storage", "logs"):
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        for child in list(directory.iterdir()):
            _remove_path(child)

    backup_root = root / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    for child in list(backup_root.iterdir()):
        if child.resolve() == protected:
            continue
        _remove_path(child)

    # Remove unrecognized active-root files/directories.  The remaining items
    # are installation/runtime infrastructure, not farm records.
    preserved = {
        "backups",
        "logs",
        "postgres",
        "security",
        "storage",
        "lifecycle.json",
        "installation_state.json",
    }
    for child in list(root.iterdir()):
        if child.name in preserved:
            continue
        _remove_path(child)

    # Keep the rollback artifact until every zero-state check has passed.  The
    # caller removes it only after verifying storage, logs and old backups.


def _clear_clean_lifecycle_backup_pointer(data_root: str | Path) -> None:
    """Remove the manifest pointer to the recovery copy deleted from active data."""
    path = Path(data_root).expanduser().resolve() / "lifecycle.json"
    if not path.is_file():
        return
    temporary: Path | None = None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("lifecycle manifest is not an object")
        payload["last_backup"] = None
        payload["updated_at"] = _utc_now()
        temporary = path.with_name(f".{path.name}.clean-tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LifecycleError(
            "Clean installation cannot clear the active lifecycle backup pointer."
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _verify_active_clean_state(
    data_root: str | Path,
    *,
    allowed_backup: str | Path | None = None,
) -> list[str]:
    root = Path(data_root).expanduser().resolve()
    allowed = (
        Path(allowed_backup).expanduser().resolve()
        if allowed_backup is not None
        else None
    )
    residual: list[str] = []
    for name in ("storage", "logs", "backups"):
        directory = root / name
        if not directory.is_dir():
            residual.append(f"{name}=missing")
        elif any(
            child.resolve() != allowed for child in directory.iterdir()
        ):
            residual.append(f"{name}=nonempty")
    return residual


def _write_audit_event(artifact: Path, event: str, payload: dict[str, object]) -> None:
    path = artifact.parent / "admin-audit.jsonl"
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, **payload}
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

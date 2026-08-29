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
from dairyos.lifecycle.reset import reset_operational_data, verify_zero_state
from dairyos.lifecycle.restore import restore_snapshot

RESET_CONFIRMATION = "RESET DAIRYOS DATA"
PURGE_CONFIRMATION = "PURGE DAIRYOS DATA"


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
        artifact = self.manager.backup(label=label)
        _record_database_checksum(artifact)
        _verify_backup_directory(artifact)
        return AdminResult("backup", True, "Backup completed and verified.", str(artifact))

    def restore(self, backup: str | Path) -> AdminResult:
        _verify_backup_directory(backup)
        restore_snapshot(self.manager, backup)
        self.manager.validate(require_database=bool(self.manager.database_url))
        return AdminResult("restore", True, "Snapshot restored and validated.", str(Path(backup).resolve()))

    def rollback(self, backup: str | Path) -> AdminResult:
        _verify_backup_directory(backup)
        result = self.manager.rollback(backup)
        return AdminResult(
            "rollback",
            bool(result.get("valid")),
            "Rollback completed and validated.",
            str(Path(backup).resolve()),
        )

    def reset(self, confirmation: str, backup_before_reset: bool = True) -> AdminResult:
        """Reset operational state through a verified external recovery point."""
        if confirmation != RESET_CONFIRMATION:
            raise LifecycleError(
                f"Reset requires the exact confirmation token: {RESET_CONFIRMATION!r}"
            )
        if not self.manager.database_url:
            raise LifecycleError("Reset requires DAIRYOS_DATABASE_URL to be configured.")

        _admin_stage("reset: runtime stopped check")
        _assert_runtime_stopped()
        _admin_stage("reset: lifecycle validation")
        self.manager.validate(require_database=True)
        _admin_stage("reset: pre-reset backup")
        artifact = self.manager.backup(label="pre-reset") if backup_before_reset else None
        if artifact is None:
            raise LifecycleError("Reset requires a verified pre-reset backup.")
        _admin_stage(f"reset: backup complete: {artifact}")
        _admin_stage("reset: recording database checksum")
        _record_database_checksum(artifact)
        _admin_stage("reset: copying external recovery artifact")
        recovery_artifact = _copy_external_recovery_artifact(artifact)
        _admin_stage(f"reset: external recovery copy complete: {recovery_artifact}")
        _admin_stage("reset: verifying recovery artifact")
        _verify_backup_directory(recovery_artifact)
        _admin_stage("reset: recording reset intent")
        _write_audit_event(recovery_artifact, "reset-intent", {"artifact": str(recovery_artifact)})
        try:
            _admin_stage("reset: destructive SQL transaction starting")
            execution = reset_operational_data(
                self.manager.database_url,
                updated_by="DairyOS Admin Tool",
            )
            _admin_stage("reset: destructive SQL transaction complete")
            remaining = verify_zero_state(self.manager.database_url)
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
                {"status": "success", "tables_cleared": list(execution.tables_cleared)},
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
                {"status": "failed", "error": str(exc)},
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
        f"DairyOS runtime is still listening on {host}:{port}. Stop the operational application before executing Reset."
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


def _verify_backup_directory(backup: str | Path) -> None:
    path = Path(backup).resolve()
    manifest_path = path / "backup.json"
    if not manifest_path.is_file():
        raise LifecycleError(f"Invalid DairyOS backup: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database_backup = manifest.get("database_backup")
    if database_backup:
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
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{backup.name}-external"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(backup, destination)
    return destination


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

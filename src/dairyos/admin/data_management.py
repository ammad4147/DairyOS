"""Farm data export and import for DairyOS portability.

Export creates a self-contained, verified ``.dairypkg`` directory containing:
  - PostgreSQL custom-format database dump.
  - Persistent operational files (storage/, security/).
  - Farm identity and profile metadata.
  - Alembic schema revision and DairyOS version.
  - SHA-256 manifest for all files.
  - Semantic fingerprint (table counts and key controls).

Import is fully transactional with pre-import rollback protection.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

from dairyos.data.database.backup import (
    PostgreSQLBackupError,
    database_semantic_fingerprint,
    verify_backup_archive,
)
from dairyos.data.database.backup import (
    create_backup as pg_create_backup,
)
from dairyos.data.database.backup import (
    restore_backup as pg_restore_backup,
)
from dairyos.data.database.session import create_application_session
from dairyos.data.farm_identity import (
    get_or_create_farm_instance_id,
    read_farm_instance_id,
    set_farm_instance_id,
)
from dairyos.platform import paths

LOG = logging.getLogger(__name__)

PACKAGE_FORMAT_VERSION = 1
PACKAGE_MANIFEST_FILENAME = "package-manifest.json"
PACKAGE_DATABASE_FILENAME = "database.dump"
PACKAGE_FILES_DIRNAME = "files"
PACKAGE_METADATA_FILENAME = "metadata.json"


def _dairyos_version() -> str:
    try:
        return package_version("dairyos")
    except PackageNotFoundError:
        return "unknown"


def _safe_package_member(package_root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise DataManagementError(f"Package manifest contains an absolute path: {relative_path}")
    resolved = (package_root / candidate).resolve()
    try:
        resolved.relative_to(package_root)
    except ValueError as exc:
        raise DataManagementError(f"Package manifest contains an unsafe path: {relative_path}") from exc
    return resolved

# Persistent directories to include in export.
_PERSISTENT_DIRS = ("storage", "security")


class DataManagementError(RuntimeError):
    """Raised when a data management operation fails."""


class ImportRefusedUnchangedError(DataManagementError):
    """PostgreSQL refused the package restore before anything was changed.

    pg_restore runs with --single-transaction and --exit-on-error, and persistent
    files are only replaced after a successful database restore. A restore
    refusal therefore leaves the farm exactly as it was, and no rollback is
    needed or attempted.
    """


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _collect_files(source_dir: Path) -> list[tuple[str, Path]]:
    """Collect all files from a directory tree, returning (relative_path, absolute_path) pairs."""
    files = []
    if source_dir.is_dir():
        for item in sorted(source_dir.rglob("*")):
            if item.is_file():
                files.append((str(item.relative_to(source_dir)), item))
    return files


def export_farm_data(
    database_url: str,
    destination: str | Path,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Create a verified, portable farm data export package.

    Returns metadata about the exported package including path, SHA-256
    hashes, and semantic fingerprint.
    """
    dest = Path(destination).expanduser().resolve()
    if dest.exists():
        raise DataManagementError(f"Export destination already exists: {dest}")
    dest.mkdir(parents=True, exist_ok=True)

    resolved_data_root = Path(data_root or paths.data_root(create=False)).resolve()
    session = create_application_session()

    try:
        # 1. Farm identity
        farm_id = get_or_create_farm_instance_id(session)
        # Do not hold the application session open while pg_dump acquires its
        # own consistent snapshot and table locks. Keeping this session alive
        # can retain a transaction on the private cluster and block export.
        session.close()
        session = None

        # 2. Database dump
        db_dump_path = dest / PACKAGE_DATABASE_FILENAME
        try:
            pg_create_backup(database_url, str(db_dump_path))
        except PostgreSQLBackupError as exc:
            raise DataManagementError(f"Database export failed: {exc}") from exc

        # 3. Verify dump archive
        try:
            archive_meta = verify_backup_archive(str(db_dump_path))
        except PostgreSQLBackupError as exc:
            raise DataManagementError(f"Database dump verification failed: {exc}") from exc

        # 4. Copy persistent files
        files_dir = dest / PACKAGE_FILES_DIRNAME
        files_dir.mkdir(exist_ok=True)
        for dirname in _PERSISTENT_DIRS:
            source = resolved_data_root / dirname
            if source.is_dir():
                shutil.copytree(source, files_dir / dirname, dirs_exist_ok=True)

        # 5. Semantic fingerprint
        fingerprint = database_semantic_fingerprint(database_url)

        # 6. Build SHA-256 manifest
        manifest_entries: dict[str, str] = {}
        manifest_entries[PACKAGE_DATABASE_FILENAME] = _sha256_file(db_dump_path)
        for rel_path, abs_path in _collect_files(files_dir):
            manifest_entries[f"{PACKAGE_FILES_DIRNAME}/{rel_path}"] = _sha256_file(abs_path)

        # 7. Metadata
        metadata = {
            "format_version": PACKAGE_FORMAT_VERSION,
            "farm_instance_id": farm_id,
            "exported_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "dairyos_version": _dairyos_version(),
            "database_file": PACKAGE_DATABASE_FILENAME,
            "semantic_fingerprint": fingerprint,
        }
        metadata_path = dest / PACKAGE_METADATA_FILENAME
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

        # 8. Package manifest (includes metadata itself)
        manifest_entries[PACKAGE_METADATA_FILENAME] = _sha256_file(metadata_path)
        manifest = {
            "format_version": PACKAGE_FORMAT_VERSION,
            "files": manifest_entries,
            "total_files": len(manifest_entries),
        }
        manifest_path = dest / PACKAGE_MANIFEST_FILENAME
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        LOG.info(
            "DairyOS farm data exported: farm_id=%s, destination=%s, files=%d",
            farm_id, dest, len(manifest_entries),
        )

        return {
            "path": str(dest),
            "farm_instance_id": farm_id,
            "total_files": len(manifest_entries),
            "database_sha256": manifest_entries[PACKAGE_DATABASE_FILENAME],
            "semantic_fingerprint": fingerprint,
            "exported_at": metadata["exported_at"],
        }
    except DataManagementError:
        # Clean up partial export on failure.
        shutil.rmtree(dest, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(dest, ignore_errors=True)
        raise DataManagementError(f"Export failed: {exc}") from exc
    finally:
        if session is not None:
            session.close()


def validate_package(package_path: str | Path) -> dict[str, Any]:
    """Validate a farm data package without modifying current farm state.

    Returns validation results including format version, farm identity,
    file integrity, and compatibility information.
    """
    pkg = Path(package_path).expanduser().resolve()
    if not pkg.is_dir():
        raise DataManagementError(f"Package path is not a directory: {pkg}")

    # 1. Check manifest
    manifest_path = pkg / PACKAGE_MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise DataManagementError(f"Package manifest not found: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise DataManagementError(f"Package manifest is corrupt: {exc}") from exc

    if manifest.get("format_version") != PACKAGE_FORMAT_VERSION:
        raise DataManagementError(
            f"Unsupported package format version: {manifest.get('format_version')}"
        )

    # 2. Verify all file SHA-256 checksums
    files = manifest.get("files", {})
    missing = []
    corrupt = []
    for rel_path, expected_sha in files.items():
        file_path = _safe_package_member(pkg, str(rel_path))
        if not file_path.is_file():
            missing.append(rel_path)
            continue
        actual_sha = _sha256_file(file_path)
        if actual_sha != expected_sha:
            corrupt.append(rel_path)

    if missing:
        raise DataManagementError(f"Package is incomplete, missing files: {missing}")
    if corrupt:
        raise DataManagementError(f"Package integrity check failed, corrupt files: {corrupt}")

    # 3. Check metadata
    metadata_path = pkg / PACKAGE_METADATA_FILENAME
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise DataManagementError(f"Package metadata is corrupt: {exc}") from exc
    if not isinstance(metadata, dict):
        raise DataManagementError("Package metadata must be a JSON object.")
    if metadata.get("format_version") != PACKAGE_FORMAT_VERSION:
        raise DataManagementError(
            f"Package metadata format version does not match: {metadata.get('format_version')}"
        )

    # 4. Verify database dump archive
    db_path = pkg / PACKAGE_DATABASE_FILENAME
    try:
        verify_backup_archive(str(db_path))
    except PostgreSQLBackupError as exc:
        raise DataManagementError(f"Database dump archive is invalid: {exc}") from exc

    return {
        "valid": True,
        "format_version": metadata.get("format_version"),
        "farm_instance_id": metadata.get("farm_instance_id"),
        "exported_at": metadata.get("exported_at"),
        "dairyos_version": metadata.get("dairyos_version"),
        "total_files": len(files),
        "semantic_fingerprint": metadata.get("semantic_fingerprint"),
    }


def _session_for(database_url: str):
    """Open a session on exactly the database this operation was given.

    Import runs in the supervisor with the private admin URL; binding the
    farm-identity reads and writes to that URL (instead of the process-wide
    application engine) keeps every step of one import on one database.
    """
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import NullPool

    from dairyos.data.database.session import (
        _connect_with_isolated_postgres_environment,
    )

    engine = create_engine(database_url, poolclass=NullPool)
    event.listen(
        engine,
        "do_connect",
        _connect_with_isolated_postgres_environment,
        retval=True,
    )
    session = Session(bind=engine)
    original_close = session.close

    def _close() -> None:
        try:
            original_close()
        finally:
            engine.dispose()

    session.close = _close  # type: ignore[method-assign]
    return session


def import_farm_data(
    database_url: str,
    package_path: str | Path,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Import farm data from a validated package with transactional rollback protection.

    Before replacing current state, creates an authoritative pre-import
    snapshot.  On any failure, atomically reverts to the pre-import state.
    """
    # Step 1: Validate
    validation = validate_package(package_path)

    pkg = Path(package_path).expanduser().resolve()
    resolved_data_root = Path(data_root or paths.data_root(create=False)).resolve()

    # Step 2: Create pre-import rollback snapshot
    rollback_dir = resolved_data_root / "backups" / "pre-import-rollback"
    if rollback_dir.exists():
        shutil.rmtree(rollback_dir)
    rollback_dir.mkdir(parents=True, exist_ok=True)
    rollback_db_path = rollback_dir / "rollback.dump"

    try:
        pg_create_backup(database_url, str(rollback_db_path))
    except PostgreSQLBackupError as exc:
        raise DataManagementError(
            f"Pre-import rollback snapshot failed; import is blocked: {exc}"
        ) from exc

    # Save current persistent files
    rollback_files_dir = rollback_dir / "files"
    rollback_files_dir.mkdir(exist_ok=True)
    for dirname in _PERSISTENT_DIRS:
        source = resolved_data_root / dirname
        if source.is_dir():
            shutil.copytree(source, rollback_files_dir / dirname, dirs_exist_ok=True)

    # Save current farm identity
    session = _session_for(database_url)
    try:
        current_farm_id = read_farm_instance_id(session)
    finally:
        session.close()

    rollback_meta = {
        "farm_instance_id": current_farm_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    (rollback_dir / "rollback-metadata.json").write_text(
        json.dumps(rollback_meta, indent=2) + "\n", encoding="utf-8"
    )

    LOG.info("DairyOS pre-import rollback snapshot created: %s", rollback_dir)

    def restore_pre_import_state() -> None:
        pg_restore_backup(database_url, str(rollback_db_path), allow_environment_password_override=False)
        for dirname in _PERSISTENT_DIRS:
            source = rollback_files_dir / dirname
            target = resolved_data_root / dirname
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
        if current_farm_id:
            rollback_session = _session_for(database_url)
            try:
                set_farm_instance_id(rollback_session, current_farm_id)
            finally:
                rollback_session.close()

    # Step 3: Perform import
    try:
        # 3a. Restore database
        db_path = pkg / PACKAGE_DATABASE_FILENAME
        try:
            pg_restore_backup(database_url, str(db_path), allow_environment_password_override=False)
        except PostgreSQLBackupError as exc:
            raise ImportRefusedUnchangedError(
                "Import refused by the database; nothing was changed. "
                f"Detail: {exc}"
            ) from exc

        # 3b. Restore persistent files
        pkg_files = pkg / PACKAGE_FILES_DIRNAME
        if pkg_files.is_dir():
            for dirname in _PERSISTENT_DIRS:
                source = pkg_files / dirname
                target = resolved_data_root / dirname
                if source.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(source, target)

        # 3c. Set farm identity from imported package
        metadata = json.loads((pkg / PACKAGE_METADATA_FILENAME).read_text(encoding="utf-8"))
        imported_farm_id = metadata.get("farm_instance_id")
        if imported_farm_id:
            session = _session_for(database_url)
            try:
                set_farm_instance_id(session, imported_farm_id)
            finally:
                session.close()

        # Step 4: Verify import
        post_fingerprint = database_semantic_fingerprint(database_url)
        expected_fingerprint = metadata.get("semantic_fingerprint", {})

        if (
            post_fingerprint.get("sha256")
            and expected_fingerprint.get("sha256")
            and post_fingerprint["sha256"] != expected_fingerprint["sha256"]
        ):
            raise DataManagementError(
                "Post-import semantic fingerprint mismatch. "
                f"Expected {expected_fingerprint.get('sha256')}, "
                f"got {post_fingerprint.get('sha256')}."
            )

        LOG.info(
            "DairyOS farm data imported successfully: farm_id=%s, source=%s",
            imported_farm_id, pkg,
        )

        # Clean up rollback snapshot on success.
        shutil.rmtree(rollback_dir, ignore_errors=True)

        return {
            "imported": True,
            "farm_instance_id": imported_farm_id,
            "source": str(pkg),
            "semantic_fingerprint": post_fingerprint,
        }

    except ImportRefusedUnchangedError:
        LOG.error("DairyOS import refused before any change; farm data untouched.")
        # The snapshot is an unneeded copy of unchanged data; remove it so it is
        # not mistaken for evidence of a partial import.
        shutil.rmtree(rollback_dir, ignore_errors=True)
        raise
    except DataManagementError:
        LOG.error("DairyOS import failed; reverting to pre-import state.")
        try:
            restore_pre_import_state()
        except Exception as revert_exc:
            LOG.critical("DairyOS CRITICAL: Failed to restore complete pre-import state: %s", revert_exc)
            raise DataManagementError(
                "Import failed and automatic rollback could not be completed. "
                f"Rollback snapshot retained at {rollback_dir}."
            ) from revert_exc
        raise
    except Exception as exc:
        LOG.error("DairyOS import failed unexpectedly; reverting to pre-import state.")
        try:
            restore_pre_import_state()
        except Exception as revert_exc:
            LOG.critical("DairyOS CRITICAL: Failed to restore complete pre-import state: %s", revert_exc)
            raise DataManagementError(
                "Import failed unexpectedly and automatic rollback could not be completed. "
                f"Rollback snapshot retained at {rollback_dir}."
            ) from revert_exc
        raise DataManagementError(f"Import failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Queued import
#
# The installed web server deliberately connects as the restricted application
# role, while every farm table belongs to the migration/admin role. pg_restore
# --clean must drop and recreate those tables, so an in-process import from
# Settings is refused by PostgreSQL ("must be owner of table ..."). Settings
# therefore validates the package and queues the import; the Windows supervisor
# applies it at the next start with the private admin authority, before the
# web server runs, exactly like the queued zero-state reset.
# ---------------------------------------------------------------------------

IMPORT_CONFIRMATION = "IMPORT VERIFIED FARM DATA"
IMPORT_REQUEST_FILENAME = "pending-farm-import.json"
IMPORT_FAILED_REQUEST_FILENAME = "pending-farm-import.failed.json"
IMPORT_RESULT_FILENAME = "farm-import-result.json"


def _import_request_path(data_root: str | Path | None = None) -> Path:
    return Path(data_root or paths.data_root(create=False)) / IMPORT_REQUEST_FILENAME


def _import_result_path(data_root: str | Path | None = None) -> Path:
    return Path(data_root or paths.data_root(create=False)) / "logs" / IMPORT_RESULT_FILENAME


def _write_json_atomically(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def queue_farm_import(
    package_path: str | Path,
    *,
    requested_by: str = "Settings Operator",
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a package now and queue its import for the next DairyOS start."""
    validation = validate_package(package_path)
    package = Path(package_path).expanduser().resolve()
    requested_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    _write_json_atomically(
        _import_request_path(data_root),
        {
            "package": str(package),
            "confirm": IMPORT_CONFIRMATION,
            "requested_by": requested_by,
            "requested_at": requested_at,
            "farm_instance_id": validation.get("farm_instance_id"),
        },
    )
    return {
        "queued": True,
        "package": str(package),
        "requested_at": requested_at,
        "farm_instance_id": validation.get("farm_instance_id"),
        "message": (
            "Farm data package validated and import queued. Close DairyOS on this PC "
            "and start it again; the import is applied during startup before anyone "
            "can use the farm, with an automatic rollback if it fails."
        ),
    }


def farm_import_status(data_root: str | Path | None = None) -> dict[str, Any]:
    """Report any queued import and the result of the last applied one."""
    root = Path(data_root or paths.data_root(create=False))
    pending = None
    request = _import_request_path(root)
    if request.is_file():
        try:
            pending = json.loads(request.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pending = {"package": None}
    last_result = None
    result = _import_result_path(root)
    if result.is_file():
        try:
            last_result = json.loads(result.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            last_result = None
    return {"pending": pending, "last_result": last_result}


def process_pending_farm_import(
    database_url: str,
    *,
    data_root: str | Path | None = None,
) -> dict[str, Any] | None:
    """Apply one queued import with admin database authority.

    Returns None when nothing is queued. When the import fails but the automatic
    rollback succeeds, the farm stays on its pre-import data, the failure is
    recorded, the request is cleared, and startup may continue. When rollback
    itself fails, the request is set aside as *.failed.json and the error is
    raised so startup is blocked for manual recovery.
    """
    root = Path(data_root or paths.data_root(create=False))
    request_path = _import_request_path(root)
    if not request_path.is_file():
        return None
    request = json.loads(request_path.read_text(encoding="utf-8"))
    base = {
        "package": request.get("package"),
        "requested_by": request.get("requested_by"),
        "requested_at": request.get("requested_at"),
    }

    def _finish(status: str, **extra: Any) -> dict[str, Any]:
        outcome = {
            **base,
            "status": status,
            "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            **extra,
        }
        _write_json_atomically(_import_result_path(root), outcome)
        return outcome

    if request.get("confirm") != IMPORT_CONFIRMATION or not request.get("package"):
        request_path.unlink(missing_ok=True)
        return _finish("REJECTED", detail="Queued import request is invalid; nothing was changed.")

    try:
        result = import_farm_data(database_url, request["package"], data_root=root)
    except DataManagementError as exc:
        detail = str(exc)
        if "rollback could not be completed" in detail:
            request_path.replace(root / IMPORT_FAILED_REQUEST_FILENAME)
            _finish("FAILED_ROLLBACK_INCOMPLETE", detail=detail)
            raise
        request_path.unlink(missing_ok=True)
        if isinstance(exc, ImportRefusedUnchangedError):
            return _finish("REFUSED_UNCHANGED", detail=detail)
        return _finish("FAILED_ROLLED_BACK", detail=detail)

    request_path.unlink(missing_ok=True)
    return _finish(
        "IMPORTED",
        farm_instance_id=result.get("farm_instance_id"),
        detail="Farm data imported and verified.",
    )

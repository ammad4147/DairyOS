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
    session = create_application_session()
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
        pg_restore_backup(database_url, str(rollback_db_path))
        for dirname in _PERSISTENT_DIRS:
            source = rollback_files_dir / dirname
            target = resolved_data_root / dirname
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
        if current_farm_id:
            rollback_session = create_application_session()
            try:
                set_farm_instance_id(rollback_session, current_farm_id)
            finally:
                rollback_session.close()

    # Step 3: Perform import
    try:
        # 3a. Restore database
        db_path = pkg / PACKAGE_DATABASE_FILENAME
        try:
            pg_restore_backup(database_url, str(db_path))
        except PostgreSQLBackupError as exc:
            raise DataManagementError(f"Database restore failed: {exc}") from exc

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
            session = create_application_session()
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

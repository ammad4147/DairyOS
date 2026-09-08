"""Shared, fail-closed validation of lifecycle snapshot file inventories."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath

from .manager import LifecycleError


def contained_file(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise LifecycleError("Backup file path must be a nonempty string.")
    name = Path(relative)
    windows = PureWindowsPath(relative)
    if (
        name.is_absolute()
        or windows.drive
        or windows.root
        or ".." in name.parts
        or ".." in windows.parts
        or ":" in relative
    ):
        raise LifecycleError("Backup contains an unsafe file path.")
    candidate = root / name
    for part in (candidate, *candidate.parents):
        if part == root.parent:
            break
        if part.is_symlink() or part.is_junction():
            raise LifecycleError("Backup contains a linked file or directory.")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise LifecycleError("Backup file points outside the snapshot.")
    if not candidate.is_file():
        raise LifecycleError("Backup file is missing.")
    return candidate


def verified_manifest(root: Path) -> dict:
    if any(part.startswith(".staging") for part in root.parts):
        raise LifecycleError("Incomplete staging backups cannot be restored.")
    manifest = json.loads(
        contained_file(root, "backup.json").read_text(encoding="utf-8")
    )
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise LifecycleError("Backup manifest must contain a file inventory list.")
    files = root / "files"
    if not files.is_dir() or files.is_symlink() or files.is_junction():
        raise LifecycleError("Snapshot files directory is missing or unsafe.")
    inventory = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise LifecycleError("Backup inventory entry must be an object.")
        source = contained_file(files, entry.get("path"))
        identity = source.resolve()
        if identity in inventory:
            raise LifecycleError("Backup inventory contains duplicate files.")
        inventory.add(identity)
        checksum = entry.get("sha256")
        if (
            not isinstance(checksum, str)
            or len(checksum) != 64
            or any(
                character not in "0123456789abcdef" for character in checksum.lower()
            )
        ):
            raise LifecycleError("Backup file is missing a valid SHA-256 checksum.")
        with source.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != checksum.lower():
            raise LifecycleError("Backup integrity check failed: SHA-256 mismatch.")
    for source in files.rglob("*"):
        if source.is_symlink() or source.is_junction():
            raise LifecycleError("Backup contains linked material.")
        if source.is_file() and source.resolve() not in inventory:
            raise LifecycleError("Backup contains unmanifested files.")
    if manifest.get("database_backup"):
        dump = contained_file(root, manifest["database_backup"])
        expected_dump = manifest.get("database_backup_sha256")
        if expected_dump:
            with dump.open("rb") as stream:
                actual_dump = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual_dump != str(expected_dump).lower():
                raise LifecycleError("Backup database SHA-256 verification failed.")
    return manifest

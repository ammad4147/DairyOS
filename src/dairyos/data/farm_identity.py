"""Durable farm identity for portable DairyOS farm-data operations."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from dairyos.platform import paths

FARM_IDENTITY_FILENAME = "farm-identity.json"
FARM_IDENTITY_SCHEMA_VERSION = 1


class FarmIdentityError(RuntimeError):
    """Raised when the durable farm identity is missing or invalid."""


def farm_identity_path(data_root: Path | None = None) -> Path:
    root = (data_root or paths.data_root(create=True)).resolve()
    return root / FARM_IDENTITY_FILENAME


def _validated_uuid(value: object) -> str:
    try:
        parsed = uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise FarmIdentityError("Farm identity contains an invalid farm_instance_id.") from exc
    if parsed.version != 4:
        raise FarmIdentityError("Farm identity must use a UUIDv4 farm_instance_id.")
    return str(parsed)


def validate_farm_identity(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise FarmIdentityError("Farm identity must be a JSON object.")
    if payload.get("schema_version") != FARM_IDENTITY_SCHEMA_VERSION:
        raise FarmIdentityError("Unsupported farm identity schema version.")
    created_at = payload.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        raise FarmIdentityError("Farm identity is missing created_at.")
    try:
        datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FarmIdentityError("Farm identity contains an invalid created_at.") from exc
    return {
        "schema_version": FARM_IDENTITY_SCHEMA_VERSION,
        "farm_instance_id": _validated_uuid(payload.get("farm_instance_id")),
        "created_at": created_at,
    }


def read_farm_identity(data_root: Path | None = None) -> dict[str, object]:
    path = farm_identity_path(data_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FarmIdentityError(f"Farm identity is missing: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise FarmIdentityError(f"Farm identity cannot be read: {path}") from exc
    return validate_farm_identity(payload)


def _write_atomically(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def ensure_farm_identity(data_root: Path | None = None) -> dict[str, object]:
    """Return the existing identity, creating it only for a genuinely new farm."""
    path = farm_identity_path(data_root)
    if path.exists():
        return read_farm_identity(data_root)
    payload = {
        "schema_version": FARM_IDENTITY_SCHEMA_VERSION,
        "farm_instance_id": str(uuid.uuid4()),
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    _write_atomically(path, payload)
    return read_farm_identity(data_root)


def install_imported_farm_identity(
    payload: object,
    *,
    data_root: Path | None = None,
    allow_replace: bool = False,
) -> dict[str, object]:
    """Install a validated imported identity only at the explicit import boundary."""
    validated = validate_farm_identity(payload)
    path = farm_identity_path(data_root)
    if path.exists() and not allow_replace:
        current = read_farm_identity(data_root)
        if current != validated:
            raise FarmIdentityError("Refusing to replace an existing farm identity.")
        return current
    _write_atomically(path, validated)
    return read_farm_identity(data_root)

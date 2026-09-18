from __future__ import annotations

import json
import uuid

import pytest

from dairyos.data.farm_identity import (
    FARM_IDENTITY_FILENAME,
    FarmIdentityError,
    ensure_farm_identity,
    install_imported_farm_identity,
    read_farm_identity,
    validate_farm_identity,
)


def test_identity_is_created_once_and_remains_stable(tmp_path):
    first = ensure_farm_identity(tmp_path)
    second = ensure_farm_identity(tmp_path)
    assert first == second
    assert uuid.UUID(str(first["farm_instance_id"])).version == 4
    assert (tmp_path / FARM_IDENTITY_FILENAME).is_file()


def test_existing_invalid_identity_is_not_silently_regenerated(tmp_path):
    (tmp_path / FARM_IDENTITY_FILENAME).write_text(
        json.dumps({"schema_version": 1, "farm_instance_id": "not-a-uuid", "created_at": "2026-09-18T00:00:00Z"}),
        encoding="utf-8",
    )
    with pytest.raises(FarmIdentityError, match="invalid farm_instance_id"):
        ensure_farm_identity(tmp_path)


def test_identity_schema_and_uuid_are_strict():
    with pytest.raises(FarmIdentityError, match="schema version"):
        validate_farm_identity({"schema_version": 2, "farm_instance_id": str(uuid.uuid4()), "created_at": "2026-09-18T00:00:00Z"})
    with pytest.raises(FarmIdentityError, match="UUIDv4"):
        validate_farm_identity({"schema_version": 1, "farm_instance_id": str(uuid.uuid1()), "created_at": "2026-09-18T00:00:00Z"})


def test_import_cannot_replace_identity_without_explicit_authority(tmp_path):
    current = ensure_farm_identity(tmp_path)
    imported = {
        "schema_version": 1,
        "farm_instance_id": str(uuid.uuid4()),
        "created_at": "2026-09-18T00:00:00Z",
    }
    with pytest.raises(FarmIdentityError, match="Refusing to replace"):
        install_imported_farm_identity(imported, data_root=tmp_path)
    assert read_farm_identity(tmp_path) == current

    installed = install_imported_farm_identity(imported, data_root=tmp_path, allow_replace=True)
    assert installed == imported

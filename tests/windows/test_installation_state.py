from __future__ import annotations

import json

import pytest

from dairyos.windows.installation_state import (
    InstallationState,
    InstallationStateError,
    inspect_installation,
    load_state,
    state_path,
    write_state,
)


def _patch_data_root(monkeypatch, tmp_path):
    root = tmp_path / "DairyOS"
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(root))
    return root


def test_fresh_machine_reports_new_installation(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    facts = inspect_installation()

    assert facts.is_new_installation is True
    assert facts.has_existing_data is False
    assert facts.state_exists is False
    assert facts.lifecycle_manifest_exists is False
    assert facts.persistent_files_exist is False
    assert facts.backup_count == 0


def test_runtime_only_directories_do_not_count_as_persistent_farm_data(
    monkeypatch,
    tmp_path,
):
    root = _patch_data_root(monkeypatch, tmp_path)

    for name in ("postgres", "logs", "backups"):
        (root / name).mkdir(parents=True, exist_ok=True)

    facts = inspect_installation()

    assert facts.is_new_installation is True
    assert facts.has_existing_data is False


def test_state_file_marks_installation_as_existing(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    write_state(
        InstallationState(
            installation_id="installation-1",
            created_at="2026-09-18T00:00:00Z",
        )
    )

    facts = inspect_installation()

    assert facts.state_exists is True
    assert facts.is_new_installation is False
    assert facts.has_existing_data is True


def test_lifecycle_manifest_marks_installation_as_existing(
    monkeypatch,
    tmp_path,
):
    root = _patch_data_root(monkeypatch, tmp_path)
    root.mkdir(parents=True)
    (root / "lifecycle.json").write_text("{}\n", encoding="utf-8")

    facts = inspect_installation()

    assert facts.lifecycle_manifest_exists is True
    assert facts.is_new_installation is False


def test_arbitrary_persistent_file_marks_installation_as_existing(
    monkeypatch,
    tmp_path,
):
    root = _patch_data_root(monkeypatch, tmp_path)
    root.mkdir(parents=True)
    (root / "farm-data.bin").write_bytes(b"farm")

    facts = inspect_installation()

    assert facts.persistent_files_exist is True
    assert facts.is_new_installation is False


def test_backup_directories_are_counted_but_do_not_alone_define_farm_data(
    monkeypatch,
    tmp_path,
):
    root = _patch_data_root(monkeypatch, tmp_path)
    (root / "backups" / "one").mkdir(parents=True)
    (root / "backups" / "two").mkdir()

    facts = inspect_installation()

    assert facts.backup_count == 2
    assert facts.persistent_files_exist is False


def test_state_round_trip_preserves_metadata(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    state = InstallationState(
        installation_id="installation-42",
        created_at="2026-09-18T00:00:00Z",
        last_started_at="2026-09-18T01:00:00Z",
        farm_initialized=True,
        database_initialized=True,
        database_name="dairyos",
        database_owner="dairyos",
    )

    target = write_state(state)

    assert target == state_path()
    assert load_state() == state


def test_load_state_returns_none_when_state_is_absent(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    assert load_state() is None


def test_load_state_rejects_invalid_json(monkeypatch, tmp_path):
    root = _patch_data_root(monkeypatch, tmp_path)
    root.mkdir(parents=True)
    (root / "installation_state.json").write_text("{", encoding="utf-8")

    with pytest.raises(InstallationStateError, match="cannot be read"):
        load_state()


def test_load_state_rejects_missing_required_metadata(monkeypatch, tmp_path):
    root = _patch_data_root(monkeypatch, tmp_path)
    root.mkdir(parents=True)
    (root / "installation_state.json").write_text(
        json.dumps({"installation_id": "installation-1"}),
        encoding="utf-8",
    )

    with pytest.raises(InstallationStateError, match="created_at"):
        load_state()


def test_installation_state_has_no_farm_launch_choice_surface():
    import dairyos.windows.installation_state as module

    retired = (
        "FarmLaunchMode",
        "require_explicit_mode",
        "validate_new_installation",
        "validate_existing_installation",
        "choose_existing_backup",
    )

    for name in retired:
        assert not hasattr(module, name)

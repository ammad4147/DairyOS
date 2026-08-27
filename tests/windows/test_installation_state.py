from __future__ import annotations

import json

import pytest

from dairyos.platform import paths
from dairyos.windows.installation_state import (
    FarmLaunchMode,
    InstallationState,
    InstallationStateError,
    choose_existing_backup,
    inspect_installation,
    load_state,
    require_explicit_mode,
    validate_existing_installation,
    validate_new_installation,
    write_state,
)


def _patch_data_root(monkeypatch, tmp_path):
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(tmp_path / "DairyOS"))


def test_fresh_machine_is_new_installation(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    facts = inspect_installation()

    assert facts.is_new_installation is True
    assert facts.has_existing_data is False
    assert facts.backup_count == 0


def test_fresh_machine_defaults_to_new(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    facts = inspect_installation()

    assert require_explicit_mode(facts, None) is FarmLaunchMode.NEW
    validate_new_installation(facts)


def test_existing_installation_requires_explicit_choice(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    root = paths.data_root(create=True)
    (root / "lifecycle.json").write_text("{}", encoding="utf-8")

    facts = inspect_installation()

    assert facts.is_new_installation is False

    with pytest.raises(InstallationStateError, match="explicit launch mode"):
        require_explicit_mode(facts, None)


def test_existing_installation_can_continue_existing_farm(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    root = paths.data_root(create=True)
    (root / "lifecycle.json").write_text("{}", encoding="utf-8")

    facts = inspect_installation()

    assert require_explicit_mode(
        facts, FarmLaunchMode.EXISTING
    ) is FarmLaunchMode.EXISTING


def test_new_farm_is_rejected_when_existing_data_is_present(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    root = paths.data_root(create=True)
    (root / "storage").mkdir(exist_ok=True)
    (root / "storage" / "farm.json").write_text("{}", encoding="utf-8")

    facts = inspect_installation()

    with pytest.raises(InstallationStateError, match="existing DairyOS data"):
        validate_new_installation(facts)


def test_restore_requires_a_backup(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    root = paths.data_root(create=True)
    (root / "lifecycle.json").write_text("{}", encoding="utf-8")

    facts = inspect_installation()

    with pytest.raises(
        InstallationStateError,
        match="no DairyOS backups are available",
    ):
        validate_existing_installation(facts, FarmLaunchMode.RESTORE)


def test_restore_selects_newest_backup(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    root = paths.data_root(create=True)
    backups = root / "backups"
    backups.mkdir(parents=True, exist_ok=True)

    older = backups / "20260826-old"
    newer = backups / "20260827-new"

    older.mkdir()
    newer.mkdir()

    older.touch()
    newer.touch()

    import os
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    facts = inspect_installation()

    assert facts.backup_count == 2
    assert choose_existing_backup(facts) == newer


def test_installation_state_round_trips(monkeypatch, tmp_path):
    _patch_data_root(monkeypatch, tmp_path)

    state = InstallationState(
        installation_id="test-installation",
        created_at="2026-08-27T00:00:00Z",
        last_started_at="2026-08-27T01:00:00Z",
        farm_initialized=True,
        database_initialized=True,
        database_name="dairyos",
        database_owner="dairyos",
    )

    state_file = write_state(state)

    assert state_file.is_file()

    loaded = load_state()

    assert loaded == state

    raw = json.loads(state_file.read_text(encoding="utf-8"))
    assert raw["installation_id"] == "test-installation"
    assert raw["farm_initialized"] is True
    assert raw["database_initialized"] is True
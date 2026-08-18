from __future__ import annotations

from pathlib import Path

import pytest

from dairyos.lifecycle.manager import (
    PURGE_CONFIRMATION,
    LifecycleManager,
    LifecycleValidationError,
    UninstallMode,
)


def _manager(tmp_path: Path) -> LifecycleManager:
    installation_root = tmp_path / "install"
    installation_root.mkdir()
    data_root = tmp_path / "data"
    return LifecycleManager(
        installation_root=installation_root,
        data_root=data_root,
    )


def test_install_creates_managed_data_layout_and_manifest(tmp_path):
    manager = _manager(tmp_path)

    manifest = manager.install(application_version="1.2.3", source_revision="abc123")

    assert manager.manifest_path.is_file()
    assert manifest.application_version == "1.2.3"
    assert (manager.data_root / "storage").is_dir()
    assert (manager.data_root / "backups").is_dir()
    assert (manager.data_root / "logs").is_dir()


def test_validate_passes_without_database_when_database_is_not_configured(tmp_path):
    manager = _manager(tmp_path)
    manager.install()

    result = manager.validate(require_database=False)

    assert result["valid"] is True
    assert result["database_checked"] is False


def test_validate_requires_manifest_and_reports_failure(tmp_path):
    manager = _manager(tmp_path)
    manager.data_root.mkdir()
    (manager.data_root / "storage").mkdir()
    (manager.data_root / "backups").mkdir()
    (manager.data_root / "logs").mkdir()

    with pytest.raises(LifecycleValidationError):
        manager.validate(require_database=False)


def test_backup_and_restore_round_trip_json_state(tmp_path):
    manager = _manager(tmp_path)
    manager.install()

    state = manager.data_root / "storage" / "operational_inputs.json"
    state.write_text('{"production_date":"2026-08-19","value":25}\n', encoding="utf-8")

    backup = manager.backup("round-trip")
    state.write_text('{"corrupted":true}\n', encoding="utf-8")

    manager.restore(backup)

    assert state.read_text(encoding="utf-8") == '{"production_date":"2026-08-19","value":25}\n'
    assert (backup / "backup.json").is_file()


def test_upgrade_restores_data_when_post_upgrade_validation_fails(tmp_path):
    manager = _manager(tmp_path)
    manager.install()

    state = manager.data_root / "storage" / "state.json"
    state.write_text('{"version":1}\n', encoding="utf-8")

    def upgrade_action():
        state.write_text('{"version":2}\n', encoding="utf-8")

    def validate_after():
        raise RuntimeError("simulated post-upgrade failure")

    with pytest.raises(RuntimeError, match="simulated post-upgrade failure"):
        manager.upgrade(upgrade_action, validate_after=validate_after)

    assert state.read_text(encoding="utf-8") == '{"version":1}\n'
    backups = list((manager.data_root / "backups").glob("*pre-upgrade"))
    assert backups


def test_uninstall_keep_data_removes_installation_but_retains_farm_data(tmp_path):
    manager = _manager(tmp_path)
    manager.install()
    keep = manager.data_root / "storage" / "keep.json"
    keep.write_text('{"keep":true}\n', encoding="utf-8")

    manager.uninstall(UninstallMode.KEEP_DATA)

    assert not manager.installation_root.exists()
    assert manager.data_root.exists()
    assert keep.is_file()


def test_uninstall_purge_requires_exact_confirmation(tmp_path):
    manager = _manager(tmp_path)
    manager.install()

    with pytest.raises(Exception, match="Permanent purge requires"):
        manager.uninstall(UninstallMode.PURGE_DATA, confirmation="NO")

    assert manager.data_root.exists()


def test_uninstall_purge_deletes_data_after_automatic_backup(tmp_path):
    manager = _manager(tmp_path)
    manager.install()
    state = manager.data_root / "storage" / "purge-me.json"
    state.write_text('{"purge":true}\n', encoding="utf-8")

    manager.uninstall(
        UninstallMode.PURGE_DATA,
        confirmation=PURGE_CONFIRMATION,
        backup_before_purge=True,
    )

    assert not manager.installation_root.exists()
    assert not manager.data_root.exists()

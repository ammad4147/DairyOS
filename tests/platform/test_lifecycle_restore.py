from pathlib import Path

import pytest

from dairyos.lifecycle.manager import LifecycleError, LifecycleManager
from dairyos.lifecycle.restore import restore_snapshot


@pytest.fixture(autouse=True)
def _isolate_database_environment(monkeypatch):
    """Keep JSON/file restore tests independent of ambient farm DB configuration."""
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)


def test_strict_restore_removes_files_created_after_backup(tmp_path: Path):
    manager = LifecycleManager(
        installation_root=tmp_path / "install",
        data_root=tmp_path / "data",
    )
    manager.install()

    original = manager.data_root / "storage" / "original.json"
    original.write_text('{"version":1}\n', encoding="utf-8")
    backup = manager.backup("strict")

    original.write_text('{"version":2}\n', encoding="utf-8")
    extra = manager.data_root / "storage" / "created-by-upgrade.json"
    extra.write_text('{"unexpected":true}\n', encoding="utf-8")

    restore_snapshot(manager, backup)

    assert original.read_text(encoding="utf-8") == '{"version":1}\n'
    assert not extra.exists()


def test_strict_restore_rejects_tampered_backup(tmp_path: Path):
    manager = LifecycleManager(
        installation_root=tmp_path / "install",
        data_root=tmp_path / "data",
    )
    manager.install()
    state = manager.data_root / "storage" / "state.json"
    state.write_text('{"safe":true}\n', encoding="utf-8")
    backup = manager.backup("integrity")

    state_backup = backup / "files" / "storage" / "state.json"
    state_backup.write_text('{"tampered":true}\n', encoding="utf-8")

    with pytest.raises(LifecycleError, match="integrity check failed"):
        restore_snapshot(manager, backup)

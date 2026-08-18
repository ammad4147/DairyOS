from pathlib import Path

from dairyos.lifecycle.manager import LifecycleManager
from dairyos.lifecycle.purge import PURGE_BACKUP_ROOT_NAME, purge_data_after_backup


def test_purge_backup_survives_data_root_deletion(tmp_path: Path):
    manager = LifecycleManager(
        installation_root=tmp_path / "install",
        data_root=tmp_path / "data",
    )
    manager.install()
    state = manager.data_root / "storage" / "important.json"
    state.write_text('{"important":true}\n', encoding="utf-8")

    backup = purge_data_after_backup(manager, create_backup=True)

    assert not manager.data_root.exists()
    assert backup is not None
    assert backup.parent.name == PURGE_BACKUP_ROOT_NAME
    restored = backup / "files" / "storage" / "important.json"
    assert restored.read_text(encoding="utf-8") == '{"important":true}\n'

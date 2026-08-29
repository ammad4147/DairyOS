from pathlib import Path

from dairyos.lifecycle.manager import LifecycleManager


def test_install_creates_installation_root(tmp_path: Path) -> None:
    installation_root = tmp_path / "install"
    data_root = tmp_path / "data"

    assert not installation_root.exists()

    manager = LifecycleManager(installation_root, data_root=data_root, database_url=None)
    manifest = manager.install(application_version="contract-test")

    assert installation_root.is_dir()
    assert Path(manifest.installation_root) == installation_root.resolve()
    assert manager.validate(require_database=False)["valid"] is True

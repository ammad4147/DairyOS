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



def test_admin_hidden_lifecycle_install_bootstraps_required_layout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from dairyos.admin import app as admin_app

    # main() applies explicit CLI roots to its process environment. This
    # in-process test must restore that environment for subsequent API tests.
    monkeypatch.setattr(admin_app.os, "environ", admin_app.os.environ.copy())

    installation_root = tmp_path / "installed"
    data_root = tmp_path / "programdata"

    monkeypatch.setattr(
        "sys.argv",
        [
            "DairyOS-Admin.exe",
            "--lifecycle-install",
            "--installation-root",
            str(installation_root),
            "--data-root",
            str(data_root),
        ],
    )

    admin_app.main()

    assert installation_root.is_dir()
    assert (data_root / "storage").is_dir()
    assert (data_root / "backups").is_dir()
    assert (data_root / "logs").is_dir()
    assert (data_root / "lifecycle.json").is_file()

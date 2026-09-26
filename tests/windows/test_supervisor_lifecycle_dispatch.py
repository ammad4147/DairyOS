import os
from types import SimpleNamespace

from dairyos.lifecycle import cli as lifecycle_cli
from dairyos.platform import paths
from dairyos.windows import private_database_security, supervisor


class _AvailableInstance:
    def acquire(self):
        return True

    def release(self):
        pass


def test_packaged_lifecycle_rejects_arbitrary_database_and_root_arguments(
    monkeypatch,
):
    monkeypatch.setattr(supervisor.sys, "frozen", True, raising=False)
    monkeypatch.setattr(supervisor, "SingleInstance", _AvailableInstance)

    assert supervisor.run_packaged_lifecycle(
        ["backup", "--database-url=postgresql://external/example"]
    ) == 64
    assert supervisor.run_packaged_lifecycle(
        ["backup", "--data-root=C:/other-farm"]
    ) == 64


def test_packaged_lifecycle_rejects_restore_outside_installation_backup_root(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(supervisor.sys, "frozen", True, raising=False)
    monkeypatch.setattr(supervisor, "SingleInstance", _AvailableInstance)
    data_root = tmp_path / "ProgramData" / "DairyOS"
    monkeypatch.setattr(paths, "data_root", lambda create=False: data_root)
    monkeypatch.setattr(
        supervisor,
        "prepare_database",
        lambda: (_ for _ in ()).throw(AssertionError("database must not start")),
    )

    assert supervisor.run_packaged_lifecycle(
        ["restore", str(tmp_path / "untrusted-backup")]
    ) == 64


def test_packaged_lifecycle_refuses_when_application_mutex_is_held(monkeypatch):
    monkeypatch.setattr(supervisor.sys, "frozen", True, raising=False)

    class HeldInstance:
        def acquire(self):
            return False

        def release(self):
            raise AssertionError("an unacquired mutex must not be released")

    monkeypatch.setattr(supervisor, "SingleInstance", HeldInstance)

    assert supervisor.run_packaged_lifecycle(["backup"]) == 73


def test_packaged_lifecycle_uses_only_this_installation_private_database(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(supervisor.sys, "frozen", True, raising=False)
    monkeypatch.setattr(supervisor, "SingleInstance", _AvailableInstance)
    executable = tmp_path / "DairyOS.exe"
    monkeypatch.setattr(supervisor.sys, "executable", str(executable))
    private_config = object()
    monkeypatch.setattr(
        supervisor,
        "prepare_database",
        lambda: SimpleNamespace(private_postgres=private_config),
    )
    monkeypatch.setattr(
        private_database_security,
        "admin_database_url",
        lambda config: "postgresql+psycopg://private-only",
    )
    data_root = tmp_path / "ProgramData" / "DairyOS"
    monkeypatch.setattr(paths, "data_root", lambda create=False: data_root)
    received: list[str] = []
    monkeypatch.setattr(
        lifecycle_cli,
        "main",
        lambda arguments: received.extend(arguments) or 0,
    )
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)

    result = supervisor.run_packaged_lifecycle(["backup", "--label", "manual"])

    assert result == 0
    assert "--database-url" not in received
    assert "--install-root" in received
    assert str(tmp_path) in received
    assert "--data-root" in received
    assert str(data_root) in received
    assert received[-2:] == ["--label", "manual"]
    assert "DAIRYOS_DATABASE_URL" not in os.environ


def test_packaged_lifecycle_output_is_logged_for_the_windowed_executable(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "ProgramData" / "DairyOS"
    monkeypatch.setattr(paths, "data_root", lambda create=True: data_root)
    monkeypatch.setattr(supervisor.sys, "stdout", None)
    monkeypatch.setattr(supervisor.sys, "stderr", None)
    monkeypatch.setattr(supervisor, "_attach_parent_console", lambda: None)
    backup_path = data_root / "backups" / "20260927T000000Z-manual"

    def fake_lifecycle(arguments):
        print(backup_path)
        return 0

    monkeypatch.setattr(supervisor, "run_packaged_lifecycle", fake_lifecycle)

    assert supervisor.main(["--lifecycle", "backup", "--label", "manual"]) == 0

    log = (data_root / "logs" / "lifecycle-cli.log").read_text(encoding="utf-8")
    assert "DairyOS lifecycle backup --label manual" in log
    assert str(backup_path) in log
    assert "finished with exit code 0" in log
    assert supervisor.sys.stdout is None
    assert supervisor.sys.stderr is None


def test_misplaced_lifecycle_flag_is_reported_in_the_lifecycle_log(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "ProgramData" / "DairyOS"
    monkeypatch.setattr(paths, "data_root", lambda create=True: data_root)
    monkeypatch.setattr(supervisor, "_attach_parent_console", lambda: None)

    assert supervisor.main(["backup", "--lifecycle"]) == 64

    log = (data_root / "logs" / "lifecycle-cli.log").read_text(encoding="utf-8")
    assert "--lifecycle must be the first command-line argument." in log
    assert "finished with exit code 64" in log

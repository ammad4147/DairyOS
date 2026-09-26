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

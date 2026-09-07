from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

from dairyos.admin.database import acquire_admin_database


def test_source_admin_uses_explicit_database_url(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg://admin@example/dairyos",
    )

    lease = acquire_admin_database(
        tmp_path / "install",
        data_root=tmp_path / "data",
    )

    assert lease.manager.database_url == "postgresql+psycopg://admin@example/dairyos"
    assert lease.stop_on_close is False


def test_frozen_admin_stops_only_private_database_it_started(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    private = SimpleNamespace()
    database = SimpleNamespace(
        private_postgres=private,
        migration_database_url="postgresql+psycopg://admin@example/dairyos",
    )
    monkeypatch.setattr(
        "dairyos.admin.database._private_database_running",
        lambda: False,
    )
    monkeypatch.setattr(
        "dairyos.windows.appliance_database.prepare_database",
        lambda: database,
    )
    stopped = []
    monkeypatch.setattr(
        "dairyos.windows.private_postgres.stop",
        lambda config: stopped.append(config),
    )

    lease = acquire_admin_database(
        tmp_path / "install",
        data_root=tmp_path / "data",
    )
    assert lease.stop_on_close is True
    assert lease.manager.database_url == database.migration_database_url

    lease.close()
    lease.close()

    assert stopped == [private]


def test_frozen_admin_does_not_stop_database_owned_by_dairyos(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    private = SimpleNamespace()
    database = SimpleNamespace(
        private_postgres=private,
        migration_database_url="postgresql+psycopg://admin@example/dairyos",
    )
    monkeypatch.setattr(
        "dairyos.admin.database._private_database_running",
        lambda: True,
    )
    monkeypatch.setattr(
        "dairyos.windows.appliance_database.prepare_database",
        lambda: database,
    )
    stopped = []
    monkeypatch.setattr(
        "dairyos.windows.private_postgres.stop",
        lambda config: stopped.append(config),
    )

    lease = acquire_admin_database(
        tmp_path / "install",
        data_root=tmp_path / "data",
    )
    assert lease.stop_on_close is False

    lease.close()

    assert stopped == []

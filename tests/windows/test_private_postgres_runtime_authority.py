from __future__ import annotations

from pathlib import Path

import pytest

from dairyos.windows import private_postgres as pg


def test_frozen_runtime_is_anchored_to_executable_and_ignores_stale_environment(
    monkeypatch,
    tmp_path,
):
    install_root = tmp_path / "installed"
    executable = install_root / "DairyOS.exe"

    monkeypatch.setattr(pg.sys, "frozen", True, raising=False)
    monkeypatch.setattr(pg.sys, "executable", str(executable))
    monkeypatch.setenv("DAIRYOS_INSTALL_ROOT", str(tmp_path / "stale-install"))
    monkeypatch.setenv(
        "DAIRYOS_PRIVATE_POSTGRES_RUNTIME",
        str(tmp_path / "stale-runtime"),
    )

    assert pg.runtime_root() == (
        install_root / "runtime" / "PostgreSQL"
    ).resolve()


def test_source_runtime_override_remains_available(monkeypatch, tmp_path):
    override = tmp_path / "postgres-runtime"
    monkeypatch.setattr(pg.sys, "frozen", False, raising=False)
    monkeypatch.setenv("DAIRYOS_PRIVATE_POSTGRES_RUNTIME", str(override))

    assert pg.runtime_root() == override.resolve()


def test_frozen_bundle_requires_nonempty_version_marker(monkeypatch, tmp_path):
    runtime = tmp_path / "runtime" / "PostgreSQL"
    runtime.mkdir(parents=True)
    monkeypatch.setattr(pg.sys, "frozen", True, raising=False)
    monkeypatch.setattr(pg, "runtime_root", lambda: runtime)

    with pytest.raises(pg.PrivatePostgreSQLError, match="version marker is missing"):
        pg.bundled_version()

    marker = runtime.parent / "postgresql.version"
    marker.write_text("\n", encoding="utf-8")
    with pytest.raises(pg.PrivatePostgreSQLError, match="version marker is empty"):
        pg.bundled_version()


def test_frozen_bundle_uses_marker_not_environment_version(monkeypatch, tmp_path):
    runtime = tmp_path / "runtime" / "PostgreSQL"
    runtime.mkdir(parents=True)
    (runtime.parent / "postgresql.version").write_text(
        "18.6\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(pg.sys, "frozen", True, raising=False)
    monkeypatch.setattr(pg, "runtime_root", lambda: runtime)
    monkeypatch.setenv("DAIRYOS_PRIVATE_POSTGRES_VERSION", "99.9")

    assert pg.bundled_version() == "18.6"


def test_initialize_cluster_allows_initdb_to_create_data_directory(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "postgres" / "data"
    data_root.mkdir(parents=True)
    calls = []

    monkeypatch.setattr(pg, "_binary", lambda name: Path(name))

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append(command)
        assert not data_root.exists()
        data_root.mkdir()
        (data_root / "PG_VERSION").write_text("18\n", encoding="utf-8")
        return Result()

    monkeypatch.setattr(pg, "_run", fake_run)

    pg.initialize_cluster(data_root=data_root, user="dairyos")

    assert calls
    assert calls[0][0] == "initdb.exe"
    assert calls[0][1:3] == ["-D", str(data_root)]
    assert (data_root / "PG_VERSION").is_file()


def test_initialize_cluster_never_removes_nonempty_data_directory(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "postgres" / "data"
    data_root.mkdir(parents=True)
    marker = data_root / "existing-farm-data"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(pg.PrivatePostgreSQLError, match="not empty"):
        pg.initialize_cluster(data_root=data_root, user="dairyos")

    assert marker.read_text(encoding="utf-8") == "preserve"

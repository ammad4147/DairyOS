"""Data-directory resolution and the server entrypoint (IM-013 Phase 0).

These exist because both modules make decisions that stay invisible until a
farm is affected by them: where records get written, and whether an upgrade
can orphan data a farm already has.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

from dairyos.platform import paths
from dairyos.platform.runtime_mode import (
    RuntimeMode,
    RuntimeModeError,
    resolve_runtime_mode,
)
from dairyos.platform.runtime_startup import (
    RuntimeStartupError,
    record_successful_start,
    run_production_startup_gates,
)
from dairyos.server import build_parser, main, resolve_configuration

# ----------------------------------------------------------------------
# Data directory resolution
# ----------------------------------------------------------------------

def test_env_override_wins_over_the_platform_default(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path / "farm"))

    assert paths.data_root() == tmp_path / "farm"
    assert paths.storage_dir() == tmp_path / "farm" / "storage"
    assert paths.backups_dir() == tmp_path / "farm" / "backups"
    assert paths.config_path() == tmp_path / "farm" / "config.json"


def test_packaged_windows_defaults_to_programdata(tmp_path, monkeypatch):
    monkeypatch.delenv(paths.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.setenv("PROGRAMDATA", str(tmp_path / "ProgramData"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert paths.data_root(create=False) == tmp_path / "ProgramData" / "DairyOS"


def test_source_windows_default_remains_localappdata(tmp_path, monkeypatch):
    monkeypatch.delenv(paths.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.setenv("PROGRAMDATA", str(tmp_path / "ProgramData"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert paths.data_root(create=False) == tmp_path / "AppData" / "Local" / "DairyOS"


def test_data_root_is_created_on_demand(tmp_path, monkeypatch):
    target = tmp_path / "not-yet-there"
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(target))

    assert not target.exists()
    assert paths.data_root().exists()


def test_describe_does_not_create_anything(tmp_path, monkeypatch):
    target = tmp_path / "untouched"
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(target))

    described = paths.describe()

    assert described["data_root"] == str(target)
    assert described["overridden_by_env"] == "True"
    assert not target.exists(), "asking where data lives must not put it there"


@pytest.mark.parametrize(
    "platform,expected_fragment",
    [
        ("win32", "DairyOS"),
        ("darwin", "Application Support"),
        ("linux", ".local"),
    ],
)
def test_platform_defaults_live_outside_the_installation(
    platform, expected_fragment, monkeypatch, tmp_path
):
    monkeypatch.delenv(paths.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    monkeypatch.setattr(sys, "platform", platform)

    root = str(paths.data_root(create=False))

    assert expected_fragment in root
    # Never inside the source or install tree: uninstalling must not be able
    # to take a farm's records with it.
    assert "site-packages" not in root


# ----------------------------------------------------------------------
# The legacy fallback — an upgrade must not orphan existing records
# ----------------------------------------------------------------------

def test_explicit_data_root_is_authoritative_over_launch_directory(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path / "managed"))
    monkeypatch.chdir(tmp_path)

    legacy = tmp_path / "data" / "storage"
    legacy.mkdir(parents=True)
    (legacy / "operational_inputs.json").write_text("[]", encoding="utf-8")

    resolved = paths.resolve_storage_file("operational_inputs.json")

    assert resolved == tmp_path / "managed" / "storage" / "operational_inputs.json"
    assert (legacy / "operational_inputs.json").read_text(encoding="utf-8") == "[]"


def test_legacy_only_storage_requires_explicit_migration(tmp_path, monkeypatch):
    monkeypatch.delenv(paths.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.setattr(paths, "_platform_data_root", lambda: tmp_path / "managed")
    monkeypatch.chdir(tmp_path)
    legacy = tmp_path / "data" / "storage"
    legacy.mkdir(parents=True)
    (legacy / "operational_inputs.json").write_text("[]", encoding="utf-8")
    with pytest.raises(RuntimeError, match="explicit migration"):
        paths.resolve_storage_file("operational_inputs.json")


def test_a_fresh_installation_uses_the_managed_location(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path / "managed"))
    monkeypatch.chdir(tmp_path)

    resolved = paths.resolve_storage_file("operational_inputs.json")

    assert resolved == tmp_path / "managed" / "storage" / "operational_inputs.json"


def test_the_managed_location_wins_once_it_holds_the_file(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path / "managed"))
    monkeypatch.chdir(tmp_path)

    legacy = tmp_path / "data" / "storage"
    legacy.mkdir(parents=True)
    (legacy / "operational_inputs.json").write_text("[]", encoding="utf-8")

    managed = paths.storage_dir()
    (managed / "operational_inputs.json").write_text("[]", encoding="utf-8")

    assert paths.resolve_storage_file("operational_inputs.json") == (
        managed / "operational_inputs.json"
    )


# ----------------------------------------------------------------------
# Server entrypoint
# ----------------------------------------------------------------------

def test_defaults_bind_to_loopback_only():
    args = build_parser().parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8000


@pytest.mark.parametrize(
    "value,expected",
    [
        ("development", RuntimeMode.DEVELOPMENT),
        ("hosted", RuntimeMode.HOSTED),
        ("browser-client", RuntimeMode.BROWSER_CLIENT),
    ],
)
def test_runtime_mode_accepts_explicit_modes(value, expected):
    assert resolve_runtime_mode(value, frozen=False) is expected


def test_explicit_windows_appliance_mode_is_accepted_on_windows():
    assert (
        resolve_runtime_mode(
            "windows-appliance", frozen=False, platform="win32"
        )
        is RuntimeMode.WINDOWS_APPLIANCE
    )


def test_frozen_windows_defaults_to_appliance_mode():
    assert (
        resolve_runtime_mode(frozen=True, platform="win32")
        is RuntimeMode.WINDOWS_APPLIANCE
    )


@pytest.mark.parametrize(
    "platform,expected",
    [
        ("win32", RuntimeMode.WINDOWS_APPLIANCE),
        ("linux", RuntimeMode.HOSTED),
    ],
)
def test_production_environment_selects_platform_runtime(
    platform, expected, monkeypatch
):
    monkeypatch.delenv("DAIRYOS_RUNTIME_MODE", raising=False)
    monkeypatch.setenv("DAIRYOS_ENV", "production")

    assert resolve_runtime_mode(frozen=False, platform=platform) is expected


def test_frozen_appliance_cannot_be_overridden_to_hosted():
    with pytest.raises(RuntimeModeError, match="cannot override"):
        resolve_runtime_mode("hosted", frozen=True, platform="win32")


def test_windows_appliance_mode_is_rejected_on_non_windows():
    with pytest.raises(RuntimeModeError, match="supported only on Windows"):
        resolve_runtime_mode("windows-appliance", frozen=False, platform="linux")


def test_frozen_non_windows_runtime_fails_clearly():
    with pytest.raises(RuntimeModeError, match="requires.*Windows"):
        resolve_runtime_mode(frozen=True, platform="linux")


def test_invalid_runtime_mode_fails_closed():
    with pytest.raises(RuntimeModeError, match="Invalid DAIRYOS_RUNTIME_MODE"):
        resolve_runtime_mode("desktop-ish", frozen=False)


def test_browser_client_mode_cannot_start_server():
    with pytest.raises(RuntimeModeError, match="frontend deployment mode"):
        resolve_configuration(build_parser().parse_args(["--runtime-mode", "browser-client"]))


def test_hosted_production_gate_uses_neutral_migration_adapter(monkeypatch):
    import builtins
    from types import SimpleNamespace

    original_import = builtins.__import__
    calls = []

    monkeypatch.setitem(
        sys.modules,
        "dairyos.platform.hosted_migrations",
        SimpleNamespace(migrate_hosted_database=lambda: calls.append("hosted")),
    )

    def deny_windows_adapter(name, *args, **kwargs):
        if name.startswith("dairyos.windows"):
            raise AssertionError("Hosted startup imported a Windows adapter.")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", deny_windows_adapter)
    run_production_startup_gates(RuntimeMode.HOSTED)
    assert calls == ["hosted"]


def test_windows_appliance_gate_still_delegates_to_windows_adapter(monkeypatch):
    import sys
    from types import SimpleNamespace

    calls = []
    adapter = SimpleNamespace(migrate_if_needed=lambda: calls.append("migrated"))
    monkeypatch.setitem(sys.modules, "dairyos.windows.migrations", adapter)

    run_production_startup_gates(RuntimeMode.WINDOWS_APPLIANCE)

    assert calls == ["migrated"]


def test_shared_entrypoints_do_not_import_windows_runtime_directly():
    from pathlib import Path

    source_root = Path(__file__).resolve().parents[2] / "src" / "dairyos"
    for relative in ("app.py", "server.py"):
        source = (source_root / relative).read_text(encoding="utf-8")
        assert "from dairyos.windows" not in source
        assert "import dairyos.windows" not in source


def test_hosted_server_entrypoint_fails_closed_before_serving(monkeypatch, capsys):
    import dairyos.server as server_module

    def block_startup(_mode):
        raise RuntimeStartupError("expected disposable test gate")

    monkeypatch.setattr(server_module, "run_production_startup_gates", block_startup)
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_RUNTIME_MODE", "development")
    exit_code = main(["--runtime-mode", "hosted"])

    assert exit_code == 1
    assert "expected disposable test gate" in capsys.readouterr().err
    assert os.environ["DAIRYOS_RUNTIME_MODE"] == "hosted"
    assert os.environ["DAIRYOS_ENV"] == "production"


def test_non_windows_modes_do_not_write_windows_install_marker():
    assert record_successful_start(RuntimeMode.HOSTED) is None


def test_data_dir_flag_is_applied_before_paths_resolve(tmp_path, monkeypatch):
    # resolve_configuration() deliberately writes DAIRYOS_DATA_DIR into the
    # real environment -- that is how the CLI flag beats the platform default.
    # Let monkeypatch own the variable so the mutation cannot outlive the test.
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, "")

    args = build_parser().parse_args(["--data-dir", str(tmp_path / "chosen")])

    configuration = resolve_configuration(args)

    assert configuration["paths"]["data_root"] == str(tmp_path / "chosen")


def test_print_config_reports_host_port_and_every_path(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, "")

    args = build_parser().parse_args(
        ["--host", "0.0.0.0", "--port", "9100", "--data-dir", str(tmp_path)]
    )

    configuration = resolve_configuration(args)

    assert configuration["host"] == "0.0.0.0"
    assert configuration["port"] == 9100
    assert set(configuration["paths"]) >= {
        "data_root",
        "storage",
        "backups",
        "logs",
        "config",
    }
    json.dumps(configuration)  # must be printable as-is

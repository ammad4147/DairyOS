"""Data-directory resolution and the server entrypoint (IM-013 Phase 0).

These exist because both modules make decisions that stay invisible until a
farm is affected by them: where records get written, and whether an upgrade
can orphan data a farm already has.
"""

from __future__ import annotations

import json
import sys

import pytest

from dairyos.platform import paths
from dairyos.server import build_parser, resolve_configuration


# ----------------------------------------------------------------------
# Data directory resolution
# ----------------------------------------------------------------------

def test_env_override_wins_over_the_platform_default(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path / "farm"))

    assert paths.data_root() == tmp_path / "farm"
    assert paths.storage_dir() == tmp_path / "farm" / "storage"
    assert paths.backups_dir() == tmp_path / "farm" / "backups"
    assert paths.config_path() == tmp_path / "farm" / "config.json"


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

def test_existing_farm_data_is_still_found_after_upgrade(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path / "managed"))
    monkeypatch.chdir(tmp_path)

    legacy = tmp_path / "data" / "storage"
    legacy.mkdir(parents=True)
    (legacy / "operational_inputs.json").write_text("[]", encoding="utf-8")

    resolved = paths.resolve_storage_file("operational_inputs.json")

    assert resolved == paths.LEGACY_STORAGE_DIR / "operational_inputs.json"


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

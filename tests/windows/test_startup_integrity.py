from __future__ import annotations

import json
from pathlib import Path

import pytest

from dairyos.windows import startup_integrity


def _set_data_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / "DairyOS"
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(root))
    monkeypatch.setenv(
        "DAIRYOS_INSTALLATION_STATE",
        str(tmp_path / "DairyOS-installation-state.json"),
    )
    return root


def test_empty_runtime_without_marker_is_allowed(monkeypatch, tmp_path):
    root = _set_data_root(monkeypatch, tmp_path)
    (root / "postgres").mkdir(parents=True)
    (root / "logs").mkdir()
    (root / "backups").mkdir()

    facts = startup_integrity.inspect_startup_integrity(
        application_tables=0,
        enforce=True,
    )

    assert facts.recovery_required is False
    assert facts.persistent_data is False
    assert facts.prior_installation is False


def test_existing_persistent_data_blocks_empty_database(monkeypatch, tmp_path):
    root = _set_data_root(monkeypatch, tmp_path)
    (root / "storage").mkdir(parents=True)
    (root / "storage" / "animal_operational_states.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(startup_integrity.StartupIntegrityError, match="Data recovery is required"):
        startup_integrity.inspect_startup_integrity(
            application_tables=0,
            enforce=True,
        )


def test_prior_successful_install_blocks_empty_database_even_when_data_root_is_gone(
    monkeypatch,
    tmp_path,
):
    root = _set_data_root(monkeypatch, tmp_path)
    marker = startup_integrity.marker_path()
    marker.write_text(
        json.dumps({"version": 1, "recorded_at": "2026-08-29T00:00:00+00:00"}) + "\n",
        encoding="utf-8",
    )

    facts = startup_integrity.inspect_startup_integrity(
        application_tables=0,
        enforce=False,
    )
    assert facts.prior_installation is True
    assert facts.persistent_data is False

    with pytest.raises(startup_integrity.StartupIntegrityError, match="will not create a new empty farm"):
        startup_integrity.inspect_startup_integrity(
            application_tables=0,
            enforce=True,
        )

    assert not root.exists()


def test_non_empty_database_is_not_blocked_by_empty_database_gate(monkeypatch, tmp_path):
    _set_data_root(monkeypatch, tmp_path)

    facts = startup_integrity.inspect_startup_integrity(
        application_tables=3,
        enforce=True,
    )

    assert facts.recovery_required is False


def test_record_successful_start_persists_marker(monkeypatch, tmp_path):
    root = _set_data_root(monkeypatch, tmp_path)
    monkeypatch.setattr(startup_integrity, "_is_packaged_windows", lambda: True)

    marker = startup_integrity.record_successful_start(data_root=root)

    assert marker is not None
    assert marker.is_file()
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["data_root"] == str(root)

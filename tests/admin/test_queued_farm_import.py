"""Settings queues farm imports; the supervisor applies them with admin authority."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from dairyos.admin import data_management as dm


def _request(root: Path, **overrides) -> Path:
    payload = {
        "package": str(root / "pkg.dairypkg"),
        "confirm": dm.IMPORT_CONFIRMATION,
        "requested_by": "Owner",
        "requested_at": "2026-09-27T00:00:00Z",
        **overrides,
    }
    path = root / dm.IMPORT_REQUEST_FILENAME
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _result(root: Path) -> dict:
    return json.loads((root / "logs" / dm.IMPORT_RESULT_FILENAME).read_text(encoding="utf-8"))


def test_queue_validates_now_and_writes_one_request(monkeypatch, tmp_path):
    monkeypatch.setattr(dm, "validate_package", lambda path: {"valid": True, "farm_instance_id": "farm-9"})
    package = tmp_path / "pkg.dairypkg"
    package.mkdir()

    outcome = dm.queue_farm_import(package, requested_by="Owner", data_root=tmp_path)

    request = json.loads((tmp_path / dm.IMPORT_REQUEST_FILENAME).read_text(encoding="utf-8"))
    assert outcome["queued"] is True
    assert request["package"] == str(package.resolve())
    assert request["confirm"] == dm.IMPORT_CONFIRMATION
    assert request["requested_by"] == "Owner"
    assert dm.farm_import_status(tmp_path)["pending"]["farm_instance_id"] == "farm-9"


def test_queue_refuses_an_invalid_package_and_queues_nothing(monkeypatch, tmp_path):
    def _invalid(path):
        raise dm.DataManagementError("manifest mismatch")

    monkeypatch.setattr(dm, "validate_package", _invalid)
    with pytest.raises(dm.DataManagementError):
        dm.queue_farm_import(tmp_path / "bad.dairypkg", data_root=tmp_path)
    assert not (tmp_path / dm.IMPORT_REQUEST_FILENAME).exists()


def test_nothing_queued_means_nothing_happens(tmp_path):
    assert dm.process_pending_farm_import("postgresql://unused", data_root=tmp_path) is None


def test_successful_import_clears_request_and_records_result(monkeypatch, tmp_path):
    _request(tmp_path)
    received = []
    monkeypatch.setattr(
        dm, "import_farm_data",
        lambda url, package, data_root=None: received.append((url, package)) or {"farm_instance_id": "farm-9"},
    )

    outcome = dm.process_pending_farm_import("postgresql://admin", data_root=tmp_path)

    assert received == [("postgresql://admin", str(tmp_path / "pkg.dairypkg"))]
    assert outcome["status"] == "IMPORTED"
    assert _result(tmp_path)["status"] == "IMPORTED"
    assert not (tmp_path / dm.IMPORT_REQUEST_FILENAME).exists()


def test_rolled_back_failure_clears_request_so_startup_continues(monkeypatch, tmp_path):
    _request(tmp_path)

    def _fail(url, package, data_root=None):
        raise dm.DataManagementError("Database restore failed: archive truncated")

    monkeypatch.setattr(dm, "import_farm_data", _fail)

    outcome = dm.process_pending_farm_import("postgresql://admin", data_root=tmp_path)

    assert outcome["status"] == "FAILED_ROLLED_BACK"
    assert "archive truncated" in outcome["detail"]
    assert not (tmp_path / dm.IMPORT_REQUEST_FILENAME).exists()


def test_incomplete_rollback_blocks_startup_and_sets_request_aside(monkeypatch, tmp_path):
    _request(tmp_path)

    def _fail(url, package, data_root=None):
        raise dm.DataManagementError(
            "Import failed and automatic rollback could not be completed. Rollback snapshot retained at X."
        )

    monkeypatch.setattr(dm, "import_farm_data", _fail)

    with pytest.raises(dm.DataManagementError):
        dm.process_pending_farm_import("postgresql://admin", data_root=tmp_path)
    assert not (tmp_path / dm.IMPORT_REQUEST_FILENAME).exists()
    assert (tmp_path / dm.IMPORT_FAILED_REQUEST_FILENAME).exists()
    assert _result(tmp_path)["status"] == "FAILED_ROLLBACK_INCOMPLETE"


def test_tampered_request_is_rejected_without_touching_data(monkeypatch, tmp_path):
    _request(tmp_path, confirm="IMPORT")
    monkeypatch.setattr(
        dm, "import_farm_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not import")),
    )

    outcome = dm.process_pending_farm_import("postgresql://admin", data_root=tmp_path)

    assert outcome["status"] == "REJECTED"
    assert not (tmp_path / dm.IMPORT_REQUEST_FILENAME).exists()


def test_export_queue_and_admin_import_round_trip_on_postgresql(tmp_path):
    """The real path: export, queue from Settings, apply with admin authority."""
    database_url = os.environ.get("DAIRYOS_DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        pytest.skip("requires the disposable PostgreSQL test database")
    data_root = tmp_path / "data"
    (data_root / "storage").mkdir(parents=True)
    (data_root / "storage" / "state.json").write_text('{"herd": 1}', encoding="utf-8")

    exported = dm.export_farm_data(database_url, tmp_path / "Farm.dairypkg", data_root=data_root)
    (data_root / "storage" / "state.json").write_text('{"herd": 2}', encoding="utf-8")
    dm.queue_farm_import(exported["path"], requested_by="Owner", data_root=data_root)

    outcome = dm.process_pending_farm_import(database_url, data_root=data_root)

    assert outcome["status"] == "IMPORTED", outcome
    assert (data_root / "storage" / "state.json").read_text(encoding="utf-8") == '{"herd": 1}'
    assert not (data_root / "backups" / "pre-import-rollback").exists()


def test_restricted_application_role_cannot_import_which_is_why_import_is_queued(tmp_path):
    """Reproduces the installed failure: 'must be owner of table ...'."""
    database_url = os.environ.get("DAIRYOS_DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        pytest.skip("requires the disposable PostgreSQL test database")
    import psycopg
    from sqlalchemy.engine import make_url

    admin = make_url(database_url)
    conninfo = dict(host=admin.host, port=admin.port, user=admin.username, dbname=admin.database)
    if admin.password:
        conninfo["password"] = admin.password
    with psycopg.connect(**conninfo, autocommit=True) as connection:
        connection.execute("DROP ROLE IF EXISTS dairyos_restricted_probe")
        connection.execute("CREATE ROLE dairyos_restricted_probe LOGIN PASSWORD 'probe'")
        connection.execute(f"GRANT CONNECT ON DATABASE {admin.database} TO dairyos_restricted_probe")
        connection.execute("GRANT USAGE ON SCHEMA public TO dairyos_restricted_probe")
        connection.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dairyos_restricted_probe")
        # Like the installed application role, which can read sequences.
        connection.execute("GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA public TO dairyos_restricted_probe")
    restricted = admin.set(username="dairyos_restricted_probe", password="probe").render_as_string(hide_password=False)
    try:
        data_root = tmp_path / "data"
        (data_root / "storage").mkdir(parents=True)
        exported = dm.export_farm_data(database_url, tmp_path / "Farm.dairypkg", data_root=data_root)

        (data_root / "storage" / "state.json").write_text('{"herd": "current"}', encoding="utf-8")
        with pytest.raises(dm.ImportRefusedUnchangedError, match="nothing was changed"):
            dm.import_farm_data(restricted, exported["path"], data_root=data_root)
        # A refused restore changes nothing, so no rollback runs and no
        # snapshot is left behind to suggest a partial import.
        assert (data_root / "storage" / "state.json").read_text(encoding="utf-8") == '{"herd": "current"}'
        assert not (data_root / "backups" / "pre-import-rollback").exists()

        # The admin authority used by the supervisor succeeds on the same package.
        dm.queue_farm_import(exported["path"], data_root=data_root)
        assert dm.process_pending_farm_import(database_url, data_root=data_root)["status"] == "IMPORTED"
    finally:
        with psycopg.connect(**conninfo, autocommit=True) as connection:
            connection.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM dairyos_restricted_probe")
            connection.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM dairyos_restricted_probe")
            connection.execute("REVOKE ALL ON SCHEMA public FROM dairyos_restricted_probe")
            connection.execute(f"REVOKE ALL ON DATABASE {admin.database} FROM dairyos_restricted_probe")
            connection.execute("DROP ROLE IF EXISTS dairyos_restricted_probe")


def test_refused_restore_is_reported_as_unchanged_and_startup_continues(monkeypatch, tmp_path):
    _request(tmp_path)

    def _refuse(url, package, data_root=None):
        raise dm.ImportRefusedUnchangedError(
            "Import refused by the database; nothing was changed. Detail: must be owner of table vaccinations"
        )

    monkeypatch.setattr(dm, "import_farm_data", _refuse)

    outcome = dm.process_pending_farm_import("postgresql://admin", data_root=tmp_path)

    assert outcome["status"] == "REFUSED_UNCHANGED"
    assert "nothing was changed" in outcome["detail"]
    assert not (tmp_path / dm.IMPORT_REQUEST_FILENAME).exists()
    assert not (tmp_path / dm.IMPORT_FAILED_REQUEST_FILENAME).exists()

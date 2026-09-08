from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dairyos.admin.service import AdminService
from dairyos.data.database.backup import create_backup, restore_backup, PostgreSQLBackupError
from dairyos.data.database.session import DATABASE_URL
from dairyos.lifecycle.manager import LifecycleManager


@pytest.fixture
def databases():
    configured = make_url(DATABASE_URL)
    assert "test" in configured.database.lower()
    maintenance = create_engine(configured.set(database="postgres"), isolation_level="AUTOCOMMIT")
    names = [f"dairyos_test_recovery_{uuid.uuid4().hex[:10]}" for _ in range(2)]
    try:
        with maintenance.connect() as connection:
            for name in names:
                connection.execute(text(f'CREATE DATABASE "{name}"'))
        urls = [configured.set(database=name).render_as_string(hide_password=False) for name in names]
        for index, url in enumerate(urls):
            engine = create_engine(url)
            try:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "CREATE TABLE event_journal ("
                            "id integer PRIMARY KEY, event_id text, event_type text, "
                            "timestamp timestamp, payload json, created_at timestamp)"
                        )
                    )
                    connection.execute(text("CREATE TABLE sentinel (value text)"))
                    connection.execute(text("INSERT INTO sentinel VALUES (:value)"), {"value": "backup" if index == 0 else "live"})
                    connection.execute(text("INSERT INTO event_journal VALUES (1, 'input-1', 'OperationalInputReceived', CURRENT_TIMESTAMP, CAST(:payload AS json))"), {"payload": json.dumps({"input_type": "equipment", "equipment_id": "BACKUP" if index == 0 else "FUTURE", "source": "audit", "actor": "audit"})})
            finally:
                engine.dispose()
        yield urls
    finally:
        with maintenance.connect() as connection:
            for name in names:
                connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        maintenance.dispose()


def _scheduled_backup(url, root):
    path = root / "DairyOS-Auto-test.dump"
    create_backup(url, path)
    path.with_suffix(".dump.json").write_text(json.dumps({
        "created_at": "2026-09-08T10:00:00Z", "file": path.name,
        "archive_verified": True, "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "kind": "ROLLING_PRIMARY",
    }))
    return path


def test_database_only_restore_preserves_settings_and_rebuilds_inputs(tmp_path, databases, monkeypatch):
    source, target = databases
    manager = LifecycleManager(tmp_path / "install", data_root=tmp_path / "farm", database_url=target)
    manager.install()
    (manager.data_root / "security").mkdir()
    settings = manager.data_root / "security/admin-settings"
    settings.write_text("keep-local-settings")
    (manager.data_root / "storage/operational_inputs.json").write_text('[{"future":true}]')
    (manager.data_root / "storage/animal_operational_states.json").write_text('[{"animal_id":"FUTURE"}]')
    backup = _scheduled_backup(source, tmp_path)
    monkeypatch.setattr("dairyos.admin.service._assert_runtime_stopped", lambda: None)
    result = AdminService(manager).restore(backup)
    assert result.success
    engine = create_engine(target)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT value FROM sentinel")).scalar_one() == "backup"
    finally:
        engine.dispose()
    assert settings.read_text() == "keep-local-settings"
    inputs = json.loads((manager.data_root / "storage/operational_inputs.json").read_text())
    assert inputs[0]["payload"]["equipment_id"] == "BACKUP"
    assert inputs[0]["event_id"] == "input-1"
    assert json.loads((manager.data_root / "storage/animal_operational_states.json").read_text()) == []
    assert list(manager.backup_root.glob("*-pre-database-restore/backup.json"))


def test_corrupt_restore_is_transactional_and_retains_live_rows(tmp_path, databases):
    source, target = databases
    backup = _scheduled_backup(source, tmp_path)
    backup.write_bytes(backup.read_bytes()[:-80])
    with pytest.raises(PostgreSQLBackupError):
        restore_backup(target, backup, allow_environment_password_override=False)
    engine = create_engine(target)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT value FROM sentinel")).scalar_one() == "live"
    finally:
        engine.dispose()


def test_database_only_projection_failure_rolls_back_database_and_files(tmp_path, databases, monkeypatch):
    source, target = databases
    manager = LifecycleManager(tmp_path / "install", data_root=tmp_path / "farm", database_url=target)
    manager.install()
    original = manager.data_root / "storage/original.txt"
    original.write_text("original")
    backup = _scheduled_backup(source, tmp_path)
    monkeypatch.setattr("dairyos.admin.service._assert_runtime_stopped", lambda: None)
    def fail(manager):
        original.write_text("partially changed")
        raise OSError("projection write failure")
    monkeypatch.setattr("dairyos.admin.database_restore.rebuild_file_projections", fail)
    with pytest.raises(Exception, match="pre-restore state retained or restored"):
        AdminService(manager).restore(backup)
    engine = create_engine(target)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT value FROM sentinel")).scalar_one() == "live"
    finally:
        engine.dispose()
    assert original.read_text() == "original"

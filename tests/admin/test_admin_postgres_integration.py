from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import pytest
import psycopg
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dairyos.admin.service import AdminService, RESET_CONFIRMATION
from dairyos.data.models.app_setting import AppSetting
from dairyos.data.models.animal import Animal
from dairyos.lifecycle.manager import LifecycleManager


pytestmark = pytest.mark.skipif(
    os.getenv("DAIRYOS_ADMIN_INTEGRATION") != "1",
    reason="set DAIRYOS_ADMIN_INTEGRATION=1 to run PostgreSQL Admin Tool integration tests",
)


def _database_url() -> str:
    explicit = os.getenv("DAIRYOS_DATABASE_URL")
    if explicit:
        return explicit
    return (
        "postgresql+psycopg://"
        f"{os.getenv('DAIRYOS_DB_USER', 'postgres')}:"
        f"{os.getenv('DAIRYOS_DB_PASSWORD', 'postgres')}@"
        f"{os.getenv('DAIRYOS_DB_HOST', 'localhost')}:"
        f"{os.getenv('DAIRYOS_DB_PORT', '5432')}/"
        f"{os.getenv('DAIRYOS_DB_NAME', 'dairyos')}"
    )


def test_admin_reset_backup_reset_and_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = _database_url()
    engine = create_engine(database_url)
    manager = LifecycleManager(tmp_path / "install", data_root=tmp_path / "data", database_url=database_url)
    manager.install(application_version="integration-test")

    animal_id = f"ADMIN-RESET-{uuid.uuid4().hex[:8].upper()}"
    try:
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE animal RESTART IDENTITY CASCADE"))
            connection.execute(
                text(
                    "INSERT INTO animal "
                    "(animal_id, animal_type, status, is_currently_milking, active, "
                    "non_milking_directive, non_milking_restore_to_milking, created_at, updated_at) "
                    "VALUES (:animal_id, 'COW', 'ACTIVE', true, true, 'NONE', false, NOW(), NOW())"
                ),
                {"animal_id": animal_id},
            )
            connection.execute(
                text(
                    "INSERT INTO app_settings (key, value, updated_at, updated_by) "
                    "VALUES ('deployment_activated', 'true', NOW(), 'integration-test') "
                    "ON CONFLICT (key) DO UPDATE SET value='true', updated_at=NOW(), updated_by='integration-test'"
                )
            )

        monkeypatch.setattr("dairyos.admin.service._assert_runtime_stopped", lambda: None)
        result = AdminService(manager).reset(RESET_CONFIRMATION)
        assert result.success is True
        recovery = Path(result.artifact)
        assert recovery.is_dir()
        assert (recovery / "database.dump").is_file()

        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM animal WHERE animal_id=:id"), {"id": animal_id}).scalar_one() == 0
            deployment = connection.execute(
                text("SELECT value FROM app_settings WHERE key='deployment_activated'")
            ).scalar_one()
            assert deployment == "false"

        manifest_text = (recovery / "backup.json").read_text(encoding="utf-8")
        assert "database_backup_sha256" in manifest_text

        postgres_url = make_url(database_url).set(database="postgres")
        restore_name = f"dairyos_restore_{uuid.uuid4().hex[:10]}"
        restore_url = make_url(database_url).set(database=restore_name)
        try:
            with psycopg.connect(str(postgres_url)) as admin_connection:
                admin_connection.autocommit = True
                admin_connection.execute('CREATE DATABASE "' + restore_name + '"')

            from dairyos.data.database.backup import restore_backup

            restore_backup(str(restore_url), recovery / "database.dump")
            restored_engine = create_engine(str(restore_url))
            try:
                with restored_engine.connect() as connection:
                    count = connection.execute(
                        text("SELECT count(*) FROM animal WHERE animal_id=:id"),
                        {"id": animal_id},
                    ).scalar_one()
                    assert count == 1
            finally:
                restored_engine.dispose()
        finally:
            with psycopg.connect(str(postgres_url)) as admin_connection:
                admin_connection.autocommit = True
                admin_connection.execute('DROP DATABASE IF EXISTS "' + restore_name + '"')
    finally:
        engine.dispose()

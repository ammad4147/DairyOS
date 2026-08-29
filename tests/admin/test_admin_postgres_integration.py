from __future__ import annotations

import os
import shutil
import sys
import uuid
from pathlib import Path

import pytest
import psycopg
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dairyos.admin.service import AdminService, RESET_CONFIRMATION
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


def _stage(message: str) -> None:
    print(f"[ADMIN-POSTGRES] {message}", file=sys.stderr, flush=True)


def test_admin_reset_backup_reset_and_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = _database_url()
    _stage("1/9 creating SQLAlchemy engine")
    engine = create_engine(database_url)
    manager = LifecycleManager(tmp_path / "install", data_root=tmp_path / "data", database_url=database_url)

    _stage("2/9 installing lifecycle manifest")
    manager.install(application_version="integration-test")

    animal_id = f"ADMIN-RESET-{uuid.uuid4().hex[:8].upper()}"
    restore_url = None
    try:
        _stage("3/9 inserting certification record")
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

        _stage("4/9 executing administrative Reset")
        result = AdminService(manager).reset(RESET_CONFIRMATION)
        assert result.success is True

        recovery = Path(result.artifact)
        assert recovery.is_dir()
        dump_path = recovery / "database.dump"
        assert dump_path.is_file()
        assert dump_path.stat().st_size > 0
        _stage(f"4/9 Reset completed; recovery artifact={recovery}")

        _stage("5/9 verifying zero-state and deployment deactivation")
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT count(*) FROM animal WHERE animal_id=:id"),
                {"id": animal_id},
            ).scalar_one() == 0
            deployment = connection.execute(
                text("SELECT value FROM app_settings WHERE key='deployment_activated'")
            ).scalar_one()
            assert deployment == "false"

        manifest_text = (recovery / "backup.json").read_text(encoding="utf-8")
        assert "database_backup_sha256" in manifest_text

        _stage("6/9 creating isolated PostgreSQL restore database")
        postgres_url = make_url(database_url).set(database="postgres")
        restore_name = f"dairyos_restore_{uuid.uuid4().hex[:10]}"
        restore_url = make_url(database_url).set(database=restore_name)
        with psycopg.connect(str(postgres_url)) as admin_connection:
            admin_connection.autocommit = True
            admin_connection.execute('CREATE DATABASE "' + restore_name + '"')

        _stage("7/9 restoring PostgreSQL dump")
        from dairyos.data.database.backup import restore_backup

        restore_backup(str(restore_url), dump_path)

        _stage("8/9 validating restored record")
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

        _stage("9/9 Reset + restore certification PASS")
    finally:
        engine.dispose()
        if restore_url is not None:
            postgres_url = make_url(database_url).set(database="postgres")
            try:
                with psycopg.connect(str(postgres_url)) as admin_connection:
                    admin_connection.autocommit = True
                    admin_connection.execute('DROP DATABASE IF EXISTS "' + restore_url.database + '"')
            except Exception as exc:
                _stage(f"restore database cleanup warning: {exc}")
        # Best-effort cleanup of any test-side temporary external artifact.
        recovery_root = tmp_path / "recovery"
        if recovery_root.exists():
            shutil.rmtree(recovery_root, ignore_errors=True)

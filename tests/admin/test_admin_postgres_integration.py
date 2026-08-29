from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
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


def _print_target_table_locks(database_url: str) -> None:
    query = """
        SELECT
            l.pid,
            a.application_name,
            a.client_addr,
            a.state,
            a.xact_start,
            l.mode,
            l.granted,
            c.relname,
            a.query
        FROM pg_locks AS l
        JOIN pg_class AS c ON c.oid = l.relation
        JOIN pg_stat_activity AS a ON a.pid = l.pid
        WHERE a.datname = current_database()
          AND c.relname IN (
              'animal', 'animal_milking_schedule_history', 'breeding_records',
              'coml_records', 'email_digest_deliveries', 'email_digest_runs',
              'equipment', 'equipment_service_events', 'event_journal', 'farms',
              'feed_inventory_items', 'feed_ration', 'feed_record',
              'financial_transactions', 'health_cases', 'health_observation',
              'inventory_transactions', 'milk_dispositions', 'milk_production',
              'milk_quality_samples', 'milking_session_records',
              'operational_events', 'operational_findings', 'operational_states',
              'treatment_record'
          )
        ORDER BY l.granted DESC, c.relname, l.pid
    """
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(query)).fetchall()
    finally:
        engine.dispose()
    if not rows:
        _stage("LOCK DIAGNOSTIC: no active locks found on Reset target tables")
        return
    for row in rows:
        _stage("LOCK DIAGNOSTIC: " + " | ".join(str(value) for value in row))


def _postgres_client_environment(database_url: str) -> tuple[make_url, dict[str, str]]:
    url = make_url(database_url)
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("DAIRYOS_DB_PASSWORD", url.password or "postgres")
    return url, env


def _run_database_utility(command: list[str], env: dict[str, str]) -> None:
    try:
        completed = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"PostgreSQL client command timed out: {' '.join(command)}") from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "PostgreSQL client command failed"
        raise AssertionError(f"{detail}: {' '.join(command)}")


def _create_database(database_url: str, database_name: str) -> None:
    """Create an isolated PostgreSQL database using the same PGPASSWORD path as CI pg_dump."""
    url, env = _postgres_client_environment(database_url)
    utility = shutil.which("createdb")
    assert utility is not None, "createdb was not installed by the PostgreSQL client package"
    command = [utility]
    if url.host:
        command += ["--host", url.host]
    if url.port:
        command += ["--port", str(url.port)]
    command += ["--username", os.getenv("DAIRYOS_DB_USER", url.username or "postgres"), database_name]
    _run_database_utility(command, env)


def _drop_database(database_url: str, database_name: str) -> None:
    """Drop the isolated PostgreSQL restore database using explicit CI credentials."""
    url, env = _postgres_client_environment(database_url)
    utility = shutil.which("dropdb")
    assert utility is not None, "dropdb was not installed by the PostgreSQL client package"
    command = [utility, "--if-exists"]
    if url.host:
        command += ["--host", url.host]
    if url.port:
        command += ["--port", str(url.port)]
    command += ["--username", os.getenv("DAIRYOS_DB_USER", url.username or "postgres"), database_name]
    _run_database_utility(command, env)


def _restore_connection_kwargs(database_url: str) -> dict[str, object]:
    url = make_url(database_url)
    return {
        "connect_args": {
            "password": os.getenv("DAIRYOS_DB_PASSWORD", url.password or "postgres")
        }
    }


def test_admin_reset_backup_reset_and_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = _database_url()
    _stage("1/9 creating SQLAlchemy engine")
    engine = create_engine(database_url)
    manager = LifecycleManager(tmp_path / "install", data_root=tmp_path / "data", database_url=database_url)

    _stage("2/9 installing lifecycle manifest")
    manager.install(application_version="integration-test")

    animal_id = f"ADMIN-RESET-{uuid.uuid4().hex[:8].upper()}"
    restore_name = None
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

        engine.dispose()
        monkeypatch.setattr("dairyos.admin.service._assert_runtime_stopped", lambda: None)
        _print_target_table_locks(database_url)

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
        verify_engine = create_engine(database_url)
        try:
            with verify_engine.connect() as connection:
                assert connection.execute(
                    text("SELECT count(*) FROM animal WHERE animal_id=:id"),
                    {"id": animal_id},
                ).scalar_one() == 0
                deployment = connection.execute(
                    text("SELECT value FROM app_settings WHERE key='deployment_activated'")
                ).scalar_one()
                assert deployment == "false"
        finally:
            verify_engine.dispose()

        manifest_text = (recovery / "backup.json").read_text(encoding="utf-8")
        assert "database_backup_sha256" in manifest_text

        _stage("6/9 creating isolated PostgreSQL restore database")
        restore_name = f"dairyos_restore_{uuid.uuid4().hex[:10]}"
        restore_url = make_url(database_url).set(database=restore_name)
        _create_database(database_url, restore_name)

        _stage("7/9 restoring PostgreSQL dump")
        from dairyos.data.database.backup import restore_backup

        restore_backup(str(restore_url), dump_path)

        _stage("8/9 validating restored record")
        restored_engine = create_engine(str(restore_url), **_restore_connection_kwargs(str(restore_url)))
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
        if restore_name is not None:
            try:
                _drop_database(database_url, restore_name)
            except Exception as exc:
                _stage(f"restore database cleanup warning: {exc}")
        recovery_root = tmp_path / "recovery"
        if recovery_root.exists():
            shutil.rmtree(recovery_root, ignore_errors=True)

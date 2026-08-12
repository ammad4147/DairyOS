from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dairyos.data.database.backup import (
    create_backup,
    restore_backup,
    verify_backup_artifact,
)
from dairyos.data.database.session import DATABASE_URL


pytestmark = pytest.mark.skipif(
    os.getenv("DAIRYOS_RUN_BACKUP_E2E") != "1",
    reason="set DAIRYOS_RUN_BACKUP_E2E=1 to run the destructive PostgreSQL restore E2E",
)


def _maintenance_url(database_url: str) -> str:
    url = make_url(database_url)
    return url.set(database="postgres").render_as_string(hide_password=False)


def _create_database(database_url: str, name: str) -> str:
    engine = create_engine(_maintenance_url(database_url), isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        engine.dispose()
    return make_url(database_url).set(database=name).render_as_string(hide_password=False)


def _drop_database(database_url: str, name: str) -> None:
    engine = create_engine(_maintenance_url(database_url), isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity WHERE datname = :name AND pid <> pg_backend_pid()"
                ),
                {"name": name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
    finally:
        engine.dispose()


def test_postgresql_backup_restore_preserves_operational_record(tmp_path: Path):
    if shutil.which("pg_dump") is None or shutil.which("pg_restore") is None:
        pytest.fail("pg_dump and pg_restore are required for the R-007 E2E test")

    source_name = f"dairyos_r007_src_{uuid.uuid4().hex[:10]}"
    target_name = f"dairyos_r007_dst_{uuid.uuid4().hex[:10]}"
    initial_backup = tmp_path / "initial.dump"
    operational_backup = tmp_path / "operational.dump"

    try:
        create_backup(DATABASE_URL, initial_backup)
        assert verify_backup_artifact(initial_backup)["size_bytes"] > 0

        source_url = _create_database(DATABASE_URL, source_name)
        target_url = _create_database(DATABASE_URL, target_name)
        restore_backup(source_url, initial_backup)

        source_engine = create_engine(source_url)
        sentinel = f"R007-{uuid.uuid4().hex}"
        try:
            with source_engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO milk_production "
                        "(animal_id, production_date, morning_yield, afternoon_yield, evening_yield, total_yield, status) "
                        "VALUES (:animal_id, CURRENT_TIMESTAMP, 10, 5, 5, 20, 'RECORDED')"
                    ),
                    {"animal_id": sentinel},
                )
                count_before = connection.execute(
                    text("SELECT COUNT(*) FROM milk_production WHERE animal_id = :animal_id"),
                    {"animal_id": sentinel},
                ).scalar_one()
        finally:
            source_engine.dispose()

        assert count_before == 1
        create_backup(source_url, operational_backup)
        restore_backup(target_url, operational_backup)

        target_engine = create_engine(target_url)
        try:
            with target_engine.connect() as connection:
                count_after = connection.execute(
                    text("SELECT COUNT(*) FROM milk_production WHERE animal_id = :animal_id"),
                    {"animal_id": sentinel},
                ).scalar_one()
        finally:
            target_engine.dispose()

        assert count_after == 1
    finally:
        _drop_database(DATABASE_URL, source_name)
        _drop_database(DATABASE_URL, target_name)

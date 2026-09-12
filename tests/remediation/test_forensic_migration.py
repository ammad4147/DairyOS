"""Exercise the incremental migration in transaction-scoped disposable schemas."""
import importlib.util
import uuid
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

from dairyos.data.database.session import engine


@pytest.mark.parametrize("invalid", [None, "nonfinite", "orphan"])
def test_incremental_migration_preserves_rows_or_blocks_without_repair(invalid):
    path = Path(__file__).resolve().parents[2] / "db_migrations/versions/20260909_02_forensic_integrity.py"
    spec = importlib.util.spec_from_file_location("forensic_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            schema = "forensic_test_" + uuid.uuid4().hex
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            statements = [
                "CREATE TABLE animal (animal_id varchar PRIMARY KEY)",
                "CREATE TABLE inventory_transactions (id int PRIMARY KEY, quantity float8 NOT NULL, signed_quantity float8 NOT NULL)",
                "CREATE TABLE feed_inventory_items (id int PRIMARY KEY, item varchar)",
                "CREATE TABLE milk_quality_samples (id int PRIMARY KEY, fat_pct float8, snf_pct float8)",
                *[f"CREATE TABLE {table} (id int PRIMARY KEY, animal_id varchar)" for table in migration.ANIMAL_LINKS],
                "INSERT INTO animal VALUES ('COW-1')",
                "INSERT INTO inventory_transactions VALUES (1,100,100)",
                "INSERT INTO feed_inventory_items VALUES (1,'silage')",
                "INSERT INTO milk_quality_samples VALUES (1,4,8.5)",
                *[f"INSERT INTO {table} VALUES (1,'COW-1')" for table in migration.ANIMAL_LINKS],
            ]
            for statement in statements:
                connection.execute(text(statement))
            if invalid == "nonfinite":
                connection.execute(text("UPDATE inventory_transactions SET quantity='NaN'::float8"))
            if invalid == "orphan":
                connection.execute(text("UPDATE feed_record SET animal_id='UNKNOWN'"))
            with Operations.context(MigrationContext.configure(connection)):
                if invalid:
                    with pytest.raises(RuntimeError, match="Integrity migration blocked"):
                        migration.upgrade()
                    assert connection.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_schema=:schema AND column_name='display_name'"), {"schema": schema}).scalar_one() == 0
                else:
                    migration.upgrade()
                    assert connection.execute(text("SELECT item,display_name FROM feed_inventory_items")).one() == ("silage", None)
                    assert connection.execute(text("SELECT fat_pct,snf_pct,revision_history FROM milk_quality_samples")).one() == (4, 8.5, [])
                    assert connection.execute(text("SELECT quantity,signed_quantity FROM inventory_transactions")).one() == (100, 100)
                    assert connection.execute(text("SELECT count(*) FROM information_schema.table_constraints WHERE constraint_schema=:schema AND constraint_type='FOREIGN KEY'"), {"schema": schema}).scalar_one() == 4
        finally:
            transaction.rollback()


def test_audit_remediation_migration_installs_new_integrity_authorities():
    path = Path(__file__).resolve().parents[2] / "db_migrations/versions/20260912_01_audit_remediation.py"
    spec = importlib.util.spec_from_file_location("audit_remediation_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            schema = "audit_remediation_test_" + uuid.uuid4().hex
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            statements = [
                "CREATE TABLE animal (animal_id varchar PRIMARY KEY)",
                "CREATE TABLE health_cases (id integer PRIMARY KEY, animal_id varchar NOT NULL)",
                "CREATE TABLE health_observation (id integer PRIMARY KEY, animal_id varchar NOT NULL, health_case_id integer)",
                "CREATE TABLE treatment_record (id integer PRIMARY KEY, animal_id varchar NOT NULL, health_case_id integer)",
                "CREATE TABLE feed_ration (id integer PRIMARY KEY, animal_group varchar NOT NULL, effective_date date NOT NULL)",
                "CREATE TABLE milk_production (id integer PRIMARY KEY)",
                "INSERT INTO animal VALUES ('COW-1')",
                "INSERT INTO health_cases VALUES (1, 'COW-1')",
                "INSERT INTO health_observation VALUES (1, 'COW-1', 1)",
                "INSERT INTO treatment_record VALUES (1, 'COW-1', 1)",
                "INSERT INTO feed_ration VALUES (1, 'TMR_DAILY_COST_SNAPSHOT', '2026-09-12')",
            ]
            for statement in statements:
                connection.execute(text(statement))

            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()

            assert connection.execute(
                text(
                    "SELECT count(*) FROM information_schema.table_constraints "
                    "WHERE table_schema=:schema AND constraint_name IN "
                    "('uq_health_cases_id_animal', "
                    "'fk_health_observation_case_same_animal', "
                    "'fk_treatment_record_case_same_animal')"
                ),
                {"schema": schema},
            ).scalar_one() == 3
            assert connection.execute(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema=:schema AND table_name="
                    "'milk_production_corrections'"
                ),
                {"schema": schema},
            ).scalar_one() == 1
            assert "uq_tmr_daily_cost_snapshot_date" in {
                index[0]
                for index in connection.execute(
                    text(
                        "SELECT indexname FROM pg_indexes "
                        "WHERE schemaname=:schema AND tablename='feed_ration'"
                    ),
                    {"schema": schema},
                )
            }
        finally:
            transaction.rollback()


def test_milk_yield_integrity_migration_rejects_stale_existing_rows():
    path = (
        Path(__file__).resolve().parents[2]
        / "db_migrations/versions/20260913_01_milk_yield_integrity.py"
    )
    spec = importlib.util.spec_from_file_location("milk_yield_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            schema = "milk_integrity_test_" + uuid.uuid4().hex
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            connection.execute(
                text(
                    "CREATE TABLE milk_production ("
                    "id integer PRIMARY KEY, "
                    "morning_yield float8, afternoon_yield float8, "
                    "evening_yield float8, total_yield float8, "
                    "session_ledger boolean NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO milk_production "
                    "VALUES (1, 10, NULL, NULL, 9, TRUE)"
                )
            )

            with Operations.context(MigrationContext.configure(connection)):
                with pytest.raises(RuntimeError, match="Milk yield integrity"):
                    migration.upgrade()

            assert connection.execute(
                text(
                    "SELECT count(*) FROM information_schema.table_constraints "
                    "WHERE table_schema=:schema AND constraint_name=:name"
                ),
                {"schema": schema, "name": migration.CONSTRAINT_NAME},
            ).scalar_one() == 0
        finally:
            transaction.rollback()


def test_milk_yield_integrity_migration_installs_constraint_for_valid_rows():
    path = (
        Path(__file__).resolve().parents[2]
        / "db_migrations/versions/20260913_01_milk_yield_integrity.py"
    )
    spec = importlib.util.spec_from_file_location("milk_yield_migration_valid", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            schema = "milk_integrity_valid_test_" + uuid.uuid4().hex
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            connection.execute(
                text(
                    "CREATE TABLE milk_production ("
                    "id integer PRIMARY KEY, "
                    "morning_yield float8, afternoon_yield float8, "
                    "evening_yield float8, total_yield float8, "
                    "session_ledger boolean NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO milk_production "
                    "VALUES (1, 10, 8, 0, 18, TRUE), "
                    "(2, NULL, NULL, NULL, NULL, TRUE), "
                    "(3, NULL, NULL, NULL, 20, FALSE)"
                )
            )

            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()

            assert connection.execute(
                text(
                    "SELECT count(*) FROM information_schema.table_constraints "
                    "WHERE table_schema=:schema AND constraint_name=:name"
                ),
                {"schema": schema, "name": migration.CONSTRAINT_NAME},
            ).scalar_one() == 1
            with pytest.raises(Exception):
                connection.execute(
                    text(
                        "INSERT INTO milk_production "
                        "VALUES (4, 10, NULL, NULL, 9, TRUE)"
                    )
                )
        finally:
            transaction.rollback()

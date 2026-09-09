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

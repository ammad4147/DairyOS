from sqlalchemy import create_engine, inspect

from dairyos.data.database import database


def test_fresh_schema_registers_health_case_and_finding_lifecycle(monkeypatch):
    """The development/test create_all boundary must include every ORM model."""
    fresh_engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(database, "engine", fresh_engine)
    monkeypatch.setenv("DAIRYOS_ENV", "test")

    database.initialize_database()

    tables = set(inspect(fresh_engine).get_table_names())
    assert "health_cases" in tables
    assert "operational_finding_lifecycle_events" in tables

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



def test_fresh_schema_registers_farm_model(monkeypatch):
    fresh_engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(database, "engine", fresh_engine)
    monkeypatch.setenv("DAIRYOS_ENV", "test")
    monkeypatch.delattr(__import__("sys"), "frozen", raising=False)

    database.initialize_database()

    tables = set(inspect(fresh_engine).get_table_names())
    assert "farms" in tables


def test_frozen_runtime_never_runs_development_create_all(monkeypatch):
    class ExplodingMetadata:
        @staticmethod
        def create_all(*args, **kwargs):
            raise AssertionError("frozen runtime must not call create_all")

    monkeypatch.setattr(database.Base, "metadata", ExplodingMetadata())
    monkeypatch.setattr(__import__("sys"), "frozen", True, raising=False)
    monkeypatch.delenv("DAIRYOS_ENV", raising=False)

    database.initialize_database()

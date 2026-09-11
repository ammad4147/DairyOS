from __future__ import annotations

import importlib
import sys

from sqlalchemy import create_engine, inspect

from dairyos.data.database import database
from dairyos.data.database.base import Base


def test_canonical_registration_contains_active_installation_schema():
    required = {
        "farms",
        "equipment",
        "equipment_service_events",
        "animal",
        "milk_production",
        "event_journal",
        "app_settings",
        "users",
    }

    assert required <= set(Base.metadata.tables)


def test_legacy_orm_modules_do_not_register_duplicate_tables():
    before = set(Base.metadata.tables)

    importlib.import_module("dairyos.core.models.farm")
    importlib.import_module("dairyos.core.models.audit_event")
    importlib.import_module(
        "dairyos.data.database.models.animal_model"
    )
    importlib.import_module(
        "dairyos.data.database.models.milk_model"
    )

    after = set(Base.metadata.tables)

    assert after == before
    assert "animals" not in after
    assert "milk_production_orm" not in after
    assert "audit_events" not in after


def test_exactly_one_farms_table_authority():
    farms = [
        mapper.class_
        for mapper in Base.registry.mappers
        if mapper.local_table.name == "farms"
    ]

    assert len(farms) == 1
    assert farms[0].__module__ == (
        "dairyos.data.database.models.farm_model"
    )
    assert farms[0].__name__ == "FarmModel"


def test_fresh_schema_contains_active_tables(monkeypatch):
    fresh = create_engine("sqlite+pysqlite:///:memory:")

    monkeypatch.setattr(database, "engine", fresh)
    monkeypatch.setenv("DAIRYOS_ENV", "test")
    monkeypatch.delattr(sys, "frozen", raising=False)

    try:
        database.initialize_database()

        tables = set(inspect(fresh).get_table_names())

        assert "farms" in tables
        assert "equipment" in tables
        assert "equipment_service_events" in tables

        assert "animals" not in tables
        assert "milk_production_orm" not in tables
        assert "audit_events" not in tables
    finally:
        fresh.dispose()


def test_frozen_runtime_never_calls_create_all(monkeypatch):
    called = False

    def forbidden_create_all(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError(
            "Frozen DairyOS must never execute development create_all()."
        )

    monkeypatch.setattr(
        database.Base.metadata,
        "create_all",
        forbidden_create_all,
    )

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("DAIRYOS_ENV", raising=False)

    database.initialize_database()

    assert called is False

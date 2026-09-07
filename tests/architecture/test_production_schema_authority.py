from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_app_startup_does_not_run_legacy_schema_migrations():
    source = _read("src/dairyos/app.py")

    forbidden = (
        "migrate_finance_feed_opex",
        "migrate_feed_inventory",
        "migrate_milk_quality",
        "migrate_coml",
        "migrate_operational_finding_audit",
        "migrate_payroll",
    )

    for name in forbidden:
        assert name not in source


def test_milk_router_import_is_schema_read_only():
    source = _read(
        "src/dairyos/api/milk_traceability.py"
    )

    assert "migrate_milk_crud" not in source


def test_governed_windows_bootstrap_owns_fresh_schema_creation():
    source = _read(
        "src/dairyos/windows/migrations.py"
    )

    assert "def _bootstrap_empty_database" in source
    assert "Base.metadata.create_all(bind=connection)" in source
    assert 'command.stamp(config, "heads")' in source
    assert "_bootstrap_empty_database(connection, config, target)" in source


def test_normal_application_initializer_is_frozen_guarded():
    source = _read(
        "src/dairyos/data/database/database.py"
    )

    assert 'getattr(sys, "frozen", False)' in source
    assert "Base.metadata.create_all(bind=engine)" in source


def test_new_alembic_authority_exists():
    source = _read(
        "db_migrations/versions/"
        "20260907_01_complete_runtime_migration_authority.py"
    )

    assert 'revision = "20260907_01"' in source
    assert 'down_revision = "20260906_04"' in source


def test_runtime_application_has_no_raw_schema_migration_import():
    source = _read("src/dairyos/app.py")

    assert (
        "from dairyos.data.database.migrations import"
        not in source
    )

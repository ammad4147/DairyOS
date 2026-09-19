from pathlib import Path

from dairyos.data.database import database  # noqa: F401 - registration boundary
from dairyos.data.database.base import Base

ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    ROOT
    / "src/dairyos/data/database/database.py"
).read_text(encoding="utf-8")


def test_database_initialization_registers_health_case():
    assert (
        "from dairyos.data.models.health_case import"
        in SOURCE
    )
    assert "HealthCase" in SOURCE


def test_database_initialization_registers_operational_finding_lifecycle():
    assert (
        "from dairyos.data.models.operational_finding_lifecycle_event import"
        in SOURCE
    )
    assert "OperationalFindingLifecycleEvent" in SOURCE


def test_database_initialization_registers_complete_runtime_model_catalog():
    """Fresh bootstrap must not depend on an unrelated import side effect."""
    expected_tables = {
        "animal",
        "animal_milking_schedule_history",
        "app_settings",
        "breeding_propagation_outbox",
        "breeding_records",
        "coml_records",
        "drug_withdrawal_reference",
        "email_digest_deliveries",
        "email_digest_runs",
        "email_sender_settings",
        "equipment",
        "equipment_service_events",
        "event_journal",
        "farms",
        "feed_inventory_items",
        "feed_ration",
        "feed_record",
        "financial_transactions",
        "health_cases",
        "health_observation",
        "inventory_transactions",
        "milk_dispositions",
        "milk_production",
        "milk_production_corrections",
        "milk_quality_samples",
        "milking_session_records",
        "operational_events",
        "operational_finding_lifecycle_events",
        "operational_findings",
        "operational_projection_outbox",
        "operational_states",
        "operational_write",
        "payroll_record",
        "semen_lots",
        "semen_stock_movements",
        "treatment_record",
        "users",
        "vaccinations",
    }

    assert set(Base.metadata.tables) == expected_tables
    assert {
        mapper.local_table.name
        for mapper in Base.registry.mappers
    } == expected_tables

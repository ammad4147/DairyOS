from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.models.feed_ration import FeedRation
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.semen_inventory import SemenStockMovement
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.farm.reproduction.services.breeding_cycle_analytics_service import (
    BreedingCycleProjectionService,
)
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    classify_animal_state,
)


ROOT = Path(__file__).resolve().parents[2]


def _fk_targets(column):
    return {fk.target_fullname for fk in column.foreign_keys}


def test_health_case_links_are_database_enforced():
    assert "health_cases.id" in _fk_targets(HealthObservation.__table__.c.health_case_id)
    assert "health_cases.id" in _fk_targets(TreatmentRecord.__table__.c.health_case_id)


def test_breeding_semen_links_are_database_enforced():
    assert "semen_lots.id" in _fk_targets(BreedingRecordModel.__table__.c.semen_lot_id)
    assert "breeding_records.record_id" in _fk_targets(
        SemenStockMovement.__table__.c.breeding_record_id
    )


def test_daily_tmr_snapshot_has_database_uniqueness():
    indexes = {index.name: index for index in FeedRation.__table__.indexes}
    assert "uq_feed_ration_daily_materialized_date" in indexes
    index = indexes["uq_feed_ration_daily_materialized_date"]
    assert index.unique
    assert [column.name for column in index.columns] == [
        "animal_group",
        "effective_date",
    ]


def test_tmr_period_read_does_not_call_storage_reconciliation():
    source = (ROOT / "src/dairyos/api/tmr.py").read_text(encoding="utf-8")
    function = source.split("def tmr_feed_cost_for_period", 1)[1].split(
        "@router.get", 1
    )[0]
    assert "reconcile_tmr_feed_storage" not in function


def test_new_service_sequence_starts_at_attempt_one_after_abortion():
    def row(record_id, event_type, day, result="RECORDED"):
        return SimpleNamespace(
            record_id=record_id,
            animal_id="A-1",
            event_type=event_type,
            result=result,
            technician="TECH",
            semen_or_bull="Conventional — SIRE",
            semen_lot_id=1,
            semen_supplier="SUPPLIER",
            semen_batch_number="BATCH",
            semen_unit_cost=1000,
            notes=None,
            timestamp=datetime(2026, 1, day, tzinfo=timezone.utc),
        )

    cycles = BreedingCycleProjectionService.project(
        [
            row("AI-1", "insemination", 1),
            row("PD-1", "pregnancy_confirmed", 2, "confirmed"),
            row("LOSS-1", "abortion", 3, "ABORTED"),
            row("AI-2", "insemination", 4),
        ]
    )
    assert [cycle["service_attempt_number"] for cycle in cycles] == [1, 1]


def test_canonical_classifier_opens_animal_after_pregnancy_loss():
    events = [
        SimpleNamespace(
            event_type="insemination",
            result="RECORDED",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
        SimpleNamespace(
            event_type="pregnancy_confirmed",
            result="confirmed",
            timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
        SimpleNamespace(
            event_type="abortion",
            result="ABORTED",
            timestamp=datetime(2026, 1, 3, tzinfo=timezone.utc),
        ),
    ]
    state = classify_animal_state(events)
    assert state["state"] == "OPEN"
    assert state["expected_calving"] is None


def test_finance_ageing_and_settlement_routes_use_operational_date_authority():
    source = (ROOT / "src/dairyos/api/finance_ledger.py").read_text(encoding="utf-8")
    ageing = source.split('def finance_ledger_ageing', 1)[1].split(
        '@router.get("/profitability', 1
    )[0]
    assert "OperationalDateAuthority" in ageing

    create = source.split("def create_finance_ledger_entry", 1)[1].split(
        "@router.patch", 1
    )[0]
    assert "OperationalDateAuthority" in create


def test_payroll_payment_rejects_nonpositive_net_pay():
    source = (ROOT / "src/dairyos/api/payroll.py").read_text(encoding="utf-8")
    payment = source.split("def _pay_payroll", 1)[1]
    assert "if net_pay <= 0:" in payment

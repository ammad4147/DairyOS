from types import SimpleNamespace

from dairyos.farm.production.services import milk_inventory_capacity_service
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)


def test_50_l_disposition_is_allowed_when_same_day_has_13_l_but_overall_has_capacity(monkeypatch):
    seen = {}

    def fake_capacity(through_date, *, exclude_disposition_id=None, factory=None):
        seen["through_date"] = through_date
        seen["exclude"] = exclude_disposition_id
        return {
            "saleable_production_litres": 113.0,
            "ordinary_accounted_litres": 20.0,
            "available_saleable_litres": 93.0,
        }

    monkeypatch.setattr(
        milk_inventory_capacity_service,
        "overall_saleable_capacity",
        fake_capacity,
    )

    MilkReconciliationService.validate_disposition_quantity(
        production_basis={
            "date": "2026-09-01",
            "saleable_litres": 13.0,
            "withdrawal_litres": 0.0,
        },
        dispositions=[],
        disposition_type="SOLD",
        quantity_litres=50.0,
    )

    assert seen["through_date"].isoformat() == "2026-09-01"
    assert seen["exclude"] is None


def test_edit_forwards_existing_row_exclusion_to_overall_capacity(monkeypatch):
    seen = {}

    def fake_capacity(through_date, *, exclude_disposition_id=None, factory=None):
        seen["exclude"] = exclude_disposition_id
        return {
            "saleable_production_litres": 60.0,
            "ordinary_accounted_litres": 0.0,
            "available_saleable_litres": 60.0,
        }

    monkeypatch.setattr(
        milk_inventory_capacity_service,
        "overall_saleable_capacity",
        fake_capacity,
    )

    existing = SimpleNamespace(
        id=7,
        status="RECORDED",
        quantity_litres=40.0,
        disposition_type="SOLD",
    )

    MilkReconciliationService.validate_disposition_quantity(
        production_basis={
            "date": "2026-09-01",
            "saleable_litres": 13.0,
            "withdrawal_litres": 0.0,
        },
        dispositions=[existing],
        disposition_type="SOLD",
        quantity_litres=50.0,
        exclude_id=7,
    )

    assert seen["exclude"] == 7

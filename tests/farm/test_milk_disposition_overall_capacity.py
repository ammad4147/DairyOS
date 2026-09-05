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



def test_reconciliation_uses_opening_carried_inventory_to_measure_only_real_overage(monkeypatch):
    from datetime import date

    service = MilkReconciliationService(
        disposition_repository=SimpleNamespace(
            get_by_date=lambda _day: [
                SimpleNamespace(
                    id=1,
                    status="RECORDED",
                    quantity_litres=304.0,
                    disposition_type="SOLD",
                    amount_due=60800.0,
                    amount_received=60800.0,
                    sale_id="FIN-1926",
                    counterparty=None,
                    selling_price_per_litre=200.0,
                    receivable_outstanding=0.0,
                    notes=None,
                    recorded_by="Finance UI",
                )
            ],
            factory=None,
        ),
        production_repository=SimpleNamespace(),
        deployment_checker=lambda: False,
    )

    monkeypatch.setattr(
        MilkReconciliationService,
        "_production_total",
        classmethod(
            lambda cls, production_date, production_repository=None: {
                "date": production_date.isoformat(),
                "complete": True,
                "has_persisted_rows": True,
                "daily_total": 261.0,
                "total_litres": 261.0,
                "saleable_litres": 261.0,
                "withdrawal_litres": 0.0,
            }
        ),
    )

    from dairyos.farm.production.services import milk_inventory_capacity_service

    monkeypatch.setattr(
        milk_inventory_capacity_service,
        "overall_saleable_capacity",
        lambda through_date, **_kwargs: {
            "available_saleable_litres": (
                40.0 if through_date == date(2026, 9, 4) else 0.0
            )
        },
    )

    result = service.reconcile(date(2026, 9, 5), raise_finding=False)

    assert result["opening_saleable_inventory_litres"] == 40.0
    assert result["over_accounted_litres"] == 3.0
    assert result["unaccounted_saleable_litres"] == 0.0
    assert result["status"] == "OVER_ACCOUNTED"


def test_reconciliation_does_not_turn_unused_opening_inventory_into_current_day_unaccounted(monkeypatch):
    from datetime import date

    service = MilkReconciliationService(
        disposition_repository=SimpleNamespace(
            get_by_date=lambda _day: [
                SimpleNamespace(
                    id=1,
                    status="RECORDED",
                    quantity_litres=280.0,
                    disposition_type="SOLD",
                    amount_due=56000.0,
                    amount_received=56000.0,
                    sale_id="FIN-TEST",
                    counterparty=None,
                    selling_price_per_litre=200.0,
                    receivable_outstanding=0.0,
                    notes=None,
                    recorded_by="Test",
                )
            ],
            factory=None,
        ),
        production_repository=SimpleNamespace(),
        deployment_checker=lambda: False,
    )

    monkeypatch.setattr(
        MilkReconciliationService,
        "_production_total",
        classmethod(
            lambda cls, production_date, production_repository=None: {
                "date": production_date.isoformat(),
                "complete": True,
                "has_persisted_rows": True,
                "daily_total": 261.0,
                "total_litres": 261.0,
                "saleable_litres": 261.0,
                "withdrawal_litres": 0.0,
            }
        ),
    )

    from dairyos.farm.production.services import milk_inventory_capacity_service

    monkeypatch.setattr(
        milk_inventory_capacity_service,
        "overall_saleable_capacity",
        lambda through_date, **_kwargs: {
            "available_saleable_litres": (
                40.0 if through_date == date(2026, 9, 4) else 0.0
            )
        },
    )

    result = service.reconcile(date(2026, 9, 5), raise_finding=False)

    assert result["opening_saleable_inventory_litres"] == 40.0
    assert result["over_accounted_litres"] == 0.0
    assert result["unaccounted_saleable_litres"] == 0.0
    assert result["status"] == "RECONCILED"

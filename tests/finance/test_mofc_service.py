from datetime import datetime, timezone
from types import SimpleNamespace

from dairyos.finance.profitability.services.mofc_service import MOFCService


def _milk(animal_id, litres, day):
    return SimpleNamespace(
        animal_id=animal_id,
        total_yield=litres,
        production_date=datetime(day.year, day.month, day.day, tzinfo=timezone.utc),
        status="RECORDED",
    )


def _feed(animal_id, quantity, cost, day, group_or_pen=None):
    return SimpleNamespace(
        animal_id=animal_id,
        group_or_pen=group_or_pen,
        quantity_kg=quantity,
        total_feed_cost=cost,
        feeding_date=datetime(day.year, day.month, day.day, tzinfo=timezone.utc),
    )


def test_mofc_uses_persisted_historical_feed_cost():
    service = MOFCService()
    now = datetime(2026, 8, 26, tzinfo=timezone.utc)

    result = service.evaluate(
        milk_records=[_milk("A-001", 20.0, now.date())],
        feed_records=[_feed("A-001", 10.0, 1500.0, now.date())],
        milk_price_per_litre=225.0,
        days=30,
        now=now,
    )

    row = result["rows"][0]
    assert row["milk_revenue"] == 4500.0
    assert row["feed_cost"] == 1500.0
    assert row["mofc"] == 3000.0
    assert row["mofc_status"] == "ACTUAL"


def test_mofc_does_not_invent_cost_for_unpriced_feed():
    service = MOFCService()
    now = datetime(2026, 8, 26, tzinfo=timezone.utc)

    result = service.evaluate(
        milk_records=[_milk("A-001", 20.0, now.date())],
        feed_records=[_feed("A-001", 10.0, None, now.date())],
        milk_price_per_litre=225.0,
        days=30,
        now=now,
    )

    row = result["rows"][0]
    assert row["unpriced_feed_quantity_kg"] == 10.0
    assert row["feed_cost"] == 0.0
    assert row["mofc"] is None
    assert row["mofc_status"] == "PARTIAL_COST_DATA"


def test_mofc_supports_group_feed_records_without_animal_id():
    service = MOFCService()
    now = datetime(2026, 8, 26, tzinfo=timezone.utc)

    result = service.evaluate(
        milk_records=[_milk("A-001", 20.0, now.date())],
        feed_records=[_feed(None, 10.0, 1500.0, now.date(), group_or_pen="MILKING_COWS")],
        milk_price_per_litre=225.0,
        days=30,
        now=now,
    )

    subjects = {row["subject_id"] for row in result["rows"]}
    assert "GROUP:MILKING_COWS" in subjects
    assert "A-001" in subjects

import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from dairyos.api.tmr import STAGE_LABELS, tmr_feed_cost_for_period
from dairyos.api.feed_inventory import reconcile_tmr_feed_storage
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.animal import Animal
from dairyos.data.models.breeding_propagation_outbox import BreedingPropagationOutbox
from dairyos.data.models.feed_ration import FeedRation
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.operations.services.daily_tmr_authority import daily_snapshots
from dairyos.farm.reproduction.services.post_calving_return_service import reconcile_due_post_calving_returns


def setup_period(monkeypatch):
    from dairyos.app import container
    from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
    today = date(2026, 9, 10)
    monkeypatch.setattr(OperationalDateAuthority, "current_date", lambda self: today)
    factory = container.repository_factory
    factory.session.add(Animal(animal_id="PERIOD", animal_type="CATTLE", sex="FEMALE",
        lifecycle_status="LACTATING", is_currently_milking=True, date_of_acquisition=date(2026, 1, 1)))
    name = "Corn / Maize Silage"
    for stage in STAGE_LABELS:
        factory.session.add(FeedRation(name=stage, animal_group=f"TMR_STAGE:{stage}",
            ingredients_json=json.dumps([{"catalog_name": name, "quantity": 2 if "milking" in stage else 1,
                "dose_unit": "kg", "fallback_price_per_kg": 10, "price_source": "FINANCE"}]),
            effective_date="2026-01-01", operator="TEST"))
    # All other catalog ingredients explicitly have zero dose.
    from dairyos.api.tmr import DEFAULT_INGREDIENTS
    for row in factory.session.new:
        if isinstance(row, FeedRation):
            ingredients = json.loads(row.ingredients_json)
            ingredients.extend({**item, "quantity": 0} for item in DEFAULT_INGREDIENTS if item["catalog_name"] != name)
            row.ingredients_json = json.dumps(ingredients)
    for day, rate in [(8, 10), (9, 20), (11, 999)]:
        factory.session.add(FinancialTransaction(transaction_type="EXPENSE", category="FEED", master_category="FEED",
            sub_category=name, amount=rate * 100, quantity=100, unit="kg", unit_rate=rate,
            transaction_date=datetime(2026, 9, day)))
    factory.session.add(EventJournalModel(event_id="lifecycle-test", event_type="OperationalInputReceived",
        timestamp=datetime(2026, 9, 9), payload={"input_type": "animal_lifecycle", "animal_id": "PERIOD",
            "timestamp": "2026-09-09", "previous_status": "DRY", "lifecycle_status": "LACTATING"}))
    factory.session.commit()
    return factory, today, name


def test_multiday_and_today_use_each_days_herd_price_and_locked_cost(client, monkeypatch):
    factory, today, _ = setup_period(monkeypatch)
    # Historical authority is created only through the explicit writer/scheduler
    # path. Reporting must never backfill it as a GET/read side effect.
    reconcile_tmr_feed_storage(
        factory,
        start_date=today - timedelta(days=2),
        end_date=today - timedelta(days=1),
    )
    result = tmr_feed_cost_for_period(factory, today - timedelta(days=2), today)
    assert [row["feed_cost"] for row in result["daily"]] == [10, 40, 40]
    assert result["total_feed_cost"] == 90
    snapshots = daily_snapshots(factory)
    before = {key: row.ingredients_json for key, row in snapshots.items()}
    factory.animal().get_by_animal_id("PERIOD").is_currently_milking = False
    factory.animal().get_by_animal_id("PERIOD").lifecycle_status = "DRY"
    factory.session.commit()
    repeated = tmr_feed_cost_for_period(factory, today - timedelta(days=2), today - timedelta(days=1))
    assert repeated["total_feed_cost"] == 50
    assert {key: row.ingredients_json for key, row in daily_snapshots(factory).items()} == before


def test_locked_legacy_daily_consumption_wins_over_reconstructed_dose(client, monkeypatch):
    factory, today, name = setup_period(monkeypatch)
    factory.session.add(InventoryTransaction(item=name, movement_type="ADJUSTMENT", quantity=3,
        signed_quantity=-3, unit="kg", recorded_by="SYSTEM_TMR",
        notes="TMR_AUTO_CONSUMPTION_DATE=2026-09-08; BASIS=LIVE_TMR"))
    factory.session.commit()
    reconcile_tmr_feed_storage(
        factory,
        start_date=today - timedelta(days=2),
        end_date=today - timedelta(days=2),
    )
    result = tmr_feed_cost_for_period(factory, today - timedelta(days=2), today - timedelta(days=2))
    assert result["total_feed_cost"] == 30
    assert len(factory.inventory().get_all()) == 1


def test_selected_period_exact_cop_formulas(client, monkeypatch):
    factory, today, _ = setup_period(monkeypatch)
    for day, liters in [(8, 10), (9, 20), (10, 30), (11, 900)]:
        factory.session.add(MilkProduction(animal_id="PERIOD", production_date=datetime(2026, 9, day), total_yield=liters))
    factory.session.add(FinancialTransaction(transaction_type="EXPENSE", category="OPEX", master_category="OPEX",
        amount=120, cop_classification="OPEX", cop_attribution_method="DIRECT",
        cop_service_date=today, transaction_date=datetime(2026, 9, 10)))
    factory.session.commit()
    reconcile_tmr_feed_storage(
        factory,
        start_date=today - timedelta(days=2),
        end_date=today - timedelta(days=1),
    )
    before = {
        key: row.ingredients_json
        for key, row in daily_snapshots(factory).items()
    }
    response = client.get("/farm/coml/integrated", params={"period_start": "2026-09-08", "period_end": "2026-09-10"})
    assert {
        key: row.ingredients_json
        for key, row in daily_snapshots(factory).items()
    } == before
    assert response.status_code == 200, response.text
    costs = response.json()["costs"]
    assert costs["feed_total"] == 90
    assert costs["opex_total"] == 120
    assert costs["feed_cost_per_liter"] == 1.5
    assert costs["opex_cost_per_liter"] == 2
    assert costs["total_coml_per_liter"] == 3.5


@pytest.mark.parametrize("source", ["outbox", "journal"])
def test_restart_reads_persisted_calving_with_empty_memory_journal(client, source):
    from dairyos.app import container
    factory = container.repository_factory
    today = date.today()
    for animal_id, offset in [("DUE", -2), ("FUTURE", 2)]:
        factory.session.add(Animal(animal_id=animal_id, animal_type="CATTLE", sex="FEMALE", lifecycle_status="DRY"))
        factory.session.flush()
        factory.animal().set_milking_frequency(animal_id, "TWICE_DAILY", reason="INITIAL", effective_date=today - timedelta(days=100), commit=False)
        payload = {"input_type": "breeding", "animal_id": animal_id, "event_type": "calving",
            "timestamp": (today - timedelta(days=5)).isoformat(),
            "planned_return_to_milking_date": (today + timedelta(days=offset)).isoformat()}
        if source == "outbox":
            factory.session.add(BreedingPropagationOutbox(propagation_id=animal_id, record_id=animal_id,
                animal_id=animal_id, event_type="calving", actor="TEST", payload=payload))
        else:
            factory.session.add(EventJournalModel(event_id=animal_id, event_type="OperationalInputReceived",
                timestamp=datetime.combine(today, datetime.min.time()), payload=payload))
    factory.session.commit()
    with Session(factory.session.get_bind()) as restarted:
        fresh = RepositoryFactory(restarted)
        empty_journal = SimpleNamespace(all_events=lambda: [])
        assert reconcile_due_post_calving_returns(fresh, empty_journal, as_of_date=today) == ["DUE"]
        assert reconcile_due_post_calving_returns(fresh, empty_journal, as_of_date=today) == []
    with Session(factory.session.get_bind()) as verification:
        fresh = RepositoryFactory(verification)
        due = fresh.animal().get_by_animal_id("DUE")
        assert due.lifecycle_status == "LACTATING" and due.is_currently_milking
        assert due.milking_frequency == "TWICE_DAILY"
        assert fresh.animal().get_by_animal_id("FUTURE").lifecycle_status == "DRY"
        history = [r for r in fresh.animal().get_milking_frequency_history("DUE") if r.reason == "POST_CALVING_PLANNED_RETURN"]
        assert len(history) == 1 and history[0].effective_from.date() == today - timedelta(days=2)

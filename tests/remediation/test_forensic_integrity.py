import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace as N

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from dairyos.data.database.session import SessionLocal
from dairyos.data.repositories.milk_quality_repository import MilkQualityRepository
from dairyos.finance.profitability.services.cost_of_production_service import (
    CostOfProductionService,
)
from dairyos.finance.profitability.services.feed_opex_cost_service import (
    FeedOpexCostService,
)
from dairyos.finance.profitability.services.mofc_service import MOFCService

NOW = datetime(2026, 9, 9, 12, tzinfo=UTC)


def milk(litres, when=NOW):
    return N(animal_id="AUDIT-COW", total_yield=litres, production_date=when, status="RECORDED")


def expense(amount, when=NOW):
    return N(amount=Decimal(amount), transaction_date=when, transaction_type="EXPENSE", category="FEED", master_category="FEED", status="RECORDED")


@pytest.mark.parametrize("service", [CostOfProductionService, FeedOpexCostService])
def test_future_records_cannot_change_period_cost(service):
    result = service().evaluate(
        [milk(100), milk(900, NOW + timedelta(days=1))],
        [expense("10000"), expense("90000", NOW + timedelta(microseconds=1))], days=1, now=NOW,
    )
    assert result["milk_litres"] == 100
    assert result["cost_per_litre"] == 100  # 10000 PKR / 100 L
    if "cmpl" in result:
        assert result["cmpl"] == 100


def test_period_includes_both_exact_boundaries_only():
    start = NOW - timedelta(days=1)
    result = CostOfProductionService().evaluate(
        [milk(40, start), milk(60), milk(900, start-timedelta(microseconds=1)), milk(900, NOW+timedelta(microseconds=1))],
        [expense("10000")], days=1, now=NOW,
    )
    assert result["milk_litres"] == 100
    assert result["cost_per_litre"] == 100


@pytest.mark.parametrize("feeds", [[], [N(animal_id="AUDIT-COW", feeding_date=NOW, quantity_kg=0, total_feed_cost=None)]])
def test_missing_or_unpriced_zero_quantity_feed_is_not_actual(feeds):
    row = MOFCService().evaluate([milk(20)], feeds, 225, days=1, now=NOW)["rows"][0]
    assert row["milk_revenue"] == 4500
    assert row["mofc"] is None
    assert row["mofc_status"] == "PARTIAL_COST_DATA"


def test_partial_day_coverage_and_void_feed_are_not_actual():
    feed = N(animal_id="AUDIT-COW", feeding_date=NOW, quantity_kg=10, total_feed_cost=100)
    row = MOFCService().evaluate([milk(20), milk(20, NOW-timedelta(days=1))], [feed], 225, days=2, now=NOW)["rows"][0]
    assert row["mofc"] is None
    feed.status = "VOID"
    row = MOFCService().evaluate([milk(20)], [feed], 225, days=1, now=NOW)["rows"][0]
    assert row["mofc"] is None


@pytest.mark.parametrize("kind", ["health_cases", "treatment_record", "breeding_records"])
def test_other_internal_animal_links_reject_orphans(kind):
    from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
    from dairyos.data.models.health_case import HealthCase
    from dairyos.data.models.treatment_record import TreatmentRecord
    rows = {
        "health_cases": HealthCase(animal_id="AUDIT-NONEXISTENT", case_id=uuid.uuid4().hex, severity="HIGH"),
        "treatment_record": TreatmentRecord(animal_id="AUDIT-NONEXISTENT", medicine="Audit", milk_withdrawal_days=0, milk_withdrawal_until=NOW.replace(tzinfo=None)),
        "breeding_records": BreedingRecordModel(animal_id="AUDIT-NONEXISTENT", record_id=uuid.uuid4().hex, event_type="insemination", result="pending", technician="Audit"),
    }
    with SessionLocal() as session:
        with pytest.raises(IntegrityError, match=f"fk_{kind}_animal"):
            session.add(rows[kind])
            session.commit()
        session.rollback()


def test_catalog_rename_preserves_identity_stock_and_unit(client):
    name = "AUDIT-" + uuid.uuid4().hex
    payload = {"item": name, "unit": "kg"}
    item = client.post("/farm/feed-inventory/items", json=payload).json()
    assert client.post("/farm/feed-inventory/movements", json={**payload, "quantity": 100, "movement_type": "RECEIPT"}).status_code == 200
    renamed = client.patch(f"/farm/feed-inventory/items/{item['id']}", json={**payload, "item": name+" renamed"})
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["item"] == name
    assert renamed.json()["display_name"] == name+" renamed"
    edited = client.patch(f"/farm/feed-inventory/items/{item['id']}", json={**payload, "location": "Bunker 2"})
    assert edited.status_code == 200
    assert edited.json()["display_name"] == name+" renamed"
    for endpoint in ("dashboard", "authoritative"):
        row = next(r for r in client.get(f"/farm/feed-inventory/{endpoint}").json()["items"] if r["id"] == item["id"])
        assert row["balance"] == 100
    response = client.patch(f"/farm/feed-inventory/items/{item['id']}", json={**payload, "unit": "tonne"})
    assert response.status_code == 409
    with SessionLocal() as session:
        assert session.execute(text("SELECT signed_quantity FROM inventory_transactions WHERE item=:item"), {"item": name}).scalar_one() == 100


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_requests_leave_no_inventory_row(client, value):
    name = "AUDIT-" + uuid.uuid4().hex
    assert client.post("/farm/feed-inventory/items", json={"item": name, "unit": "kg"}).status_code == 200
    for path in ("/farm/feed-inventory/movements", "/farm/inventory"):
        response = client.post(path, json={"item": name, "unit": "kg", "quantity": value, "movement_type": "RECEIPT", "operator": "Audit"})
        assert response.status_code == 422, response.text
    with SessionLocal() as session:
        assert session.execute(text("SELECT count(*) FROM inventory_transactions WHERE item=:item"), {"item": name}).scalar_one() == 0


def test_mixed_mass_units_preserve_physical_quantity(client):
    name = "AUDIT-" + uuid.uuid4().hex
    for quantity, unit in [(100, "kg"), (1, "tonne")]:
        response = client.post("/farm/inventory", json={"item": name, "quantity": quantity, "unit": unit, "movement_type": "RECEIPT", "operator": "Audit"})
        assert response.status_code == 200, response.text
    row = client.get("/farm/inventory/balance").json()["items"][name]
    # Both possible display units must represent precisely 100 + 1000 kg.
    assert row["balance"] * (1000 if row["unit"] == "tonne" else 1) == 1100


def test_quality_correction_preserves_original_actor_and_measurements():
    day = date(2026, 9, 2)
    with SessionLocal() as session:
        repo = MilkQualityRepository(session)
        repo.upsert(quality_date=day, fat_pct=4, snf_pct=8.5, sample_type="BULK_TANK", notes="original", recorded_by="Farmer A")
        repo.upsert(quality_date=day, fat_pct=5, snf_pct=9, sample_type="BULK_TANK", notes="correction", recorded_by="Farmer B")
    with SessionLocal() as session:
        row = MilkQualityRepository(session).get_by_date(day)
        original = row.revision_history[-1]
        assert (original["fat_pct"], original["snf_pct"], original["recorded_by"]) == (4, 8.5, "Farmer A")
        assert (row.fat_pct, row.snf_pct, row.recorded_by) == (5, 9, "Farmer B")


def test_database_rejects_orphan_feed():
    with SessionLocal() as session:
        with pytest.raises(IntegrityError):
            session.execute(text("INSERT INTO feed_record (animal_id,feed_type,quantity_kg,feeding_date) VALUES ('AUDIT-NONEXISTENT','silage',10,now())"))
            session.commit()
        session.rollback()


@pytest.mark.parametrize("column", ["quantity", "signed_quantity"])
def test_database_rejects_nonfinite_inventory(column):
    with SessionLocal() as session:
        with pytest.raises(IntegrityError):
            session.execute(text(f"INSERT INTO inventory_transactions (item,movement_type,quantity,signed_quantity,recorded_at) VALUES ('AUDIT','RECEIPT',{'\'NaN\'::float8' if column == 'quantity' else '1'},{'\'NaN\'::float8' if column == 'signed_quantity' else '1'},now())"))
            session.commit()
        session.rollback()


def test_production_session_blocks_uncredentialed_reads_and_writes(client, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_DESKTOP_SESSION_TOKEN", "audit-private-session")
    assert client.get("/health").status_code == 200
    assert client.get("/farm/feed-inventory/items").status_code == 401
    assert client.post("/farm/feed-inventory/items", json={"item": "UNAUTHORIZED"}).status_code == 401
    assert client.get("/farm/feed-inventory/items", headers={"X-DairyOS-Desktop-Session": "wrong"}).status_code == 401
    headers = {"X-DairyOS-Desktop-Session": "audit-private-session"}
    assert client.get("/farm/feed-inventory/items", headers=headers).status_code == 200
    assert client.get("/farm/feed-inventory/items", headers={**headers, "Origin": "http://attacker.invalid"}).status_code == 403


def test_concurrent_stock_corrections_cannot_spend_the_same_stock(client):
    from concurrent.futures import ThreadPoolExecutor

    from fastapi.testclient import TestClient

    from dairyos.app import app
    name = "AUDIT-" + uuid.uuid4().hex
    client.post("/farm/feed-inventory/items", json={"item": name, "unit": "kg"}).raise_for_status()
    client.post("/farm/feed-inventory/movements", json={"item": name, "unit": "kg", "quantity": 100, "movement_type": "RECEIPT"}).raise_for_status()

    def correct(_):
        concurrent_client = TestClient(app)
        try:
            return concurrent_client.post("/farm/feed-inventory/manual-override", json={"item": name, "quantity_delta": -70, "notes": "physical count"}).status_code
        finally:
            concurrent_client.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(correct, range(2)))
    assert statuses == [200, 409]
    with SessionLocal() as session:
        assert session.execute(text("SELECT sum(signed_quantity) FROM inventory_transactions WHERE item=:item"), {"item": name}).scalar_one() == 30


def test_incompatible_inventory_units_reject_before_commit(client):
    name = "AUDIT-" + uuid.uuid4().hex
    payload = {"item": name, "quantity": 100, "unit": "kg", "movement_type": "RECEIPT", "operator": "Audit"}
    assert client.post("/farm/inventory", json=payload).status_code == 200
    response = client.post("/farm/inventory", json={**payload, "unit": "bag"})
    assert response.status_code == 409, response.text
    with SessionLocal() as session:
        assert session.execute(text("SELECT count(*) FROM inventory_transactions WHERE item=:item"), {"item": name}).scalar_one() == 1

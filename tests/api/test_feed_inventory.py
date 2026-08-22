from fastapi.testclient import TestClient
import pytest

from dairyos.app import app
from dairyos.data.database.session import SessionLocal
from dairyos.data.models.feed_inventory_item import FeedInventoryItem
from dairyos.data.models.inventory_transaction import InventoryTransaction


@pytest.fixture(autouse=True)
def clean_inventory_rows():
    session = SessionLocal()
    try:
        session.query(InventoryTransaction).delete(synchronize_session=False)
        session.query(FeedInventoryItem).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()
    yield
    session = SessionLocal()
    try:
        session.query(InventoryTransaction).delete(synchronize_session=False)
        session.query(FeedInventoryItem).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


client = TestClient(app)


def create_item(**overrides):
    payload = {
        "item": "Corn / Maize Silage",
        "category": "SILAGE",
        "unit": "kg",
        "location": "Bunker 1",
        "reorder_level": 1000,
        "active": True,
    }
    payload.update(overrides)
    return client.post("/farm/feed-inventory/items", json=payload)


def move(**overrides):
    payload = {
        "item": "Corn / Maize Silage",
        "movement_type": "PURCHASE",
        "quantity": 2500,
        "unit": "kg",
    }
    payload.update(overrides)
    return client.post("/farm/feed-inventory/movements", json=payload)


def test_create_catalog_item_and_dashboard_balance():
    created = create_item()
    assert created.status_code == 200, created.text

    movement = move()
    assert movement.status_code == 200, movement.text

    dashboard = client.get("/farm/feed-inventory/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    row = dashboard.json()["items"][0]
    assert row["item"] == "Corn / Maize Silage"
    assert row["balance"] == 2500
    assert row["reorder_level"] == 1000
    assert row["status"] == "OK"


def test_duplicate_catalog_item_rejected():
    assert create_item().status_code == 200
    duplicate = create_item()
    assert duplicate.status_code == 409


def test_unit_mismatch_is_rejected():
    assert create_item().status_code == 200
    response = move(unit="ton")
    assert response.status_code == 422
    assert "Unit mismatch" in response.json()["detail"]


def test_consumption_cannot_drive_stock_negative():
    assert create_item().status_code == 200
    assert move().status_code == 200

    response = move(movement_type="CONSUMPTION", quantity=2501)
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "INSUFFICIENT_STOCK"

    dashboard = client.get("/farm/feed-inventory/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["items"][0]["balance"] == 2500


def test_consumption_updates_balance_and_low_stock_status():
    assert create_item(reorder_level=1000).status_code == 200
    assert move().status_code == 200

    response = move(movement_type="CONSUMPTION", quantity=1700)
    assert response.status_code == 200, response.text

    dashboard = client.get("/farm/feed-inventory/dashboard")
    row = dashboard.json()["items"][0]
    assert row["balance"] == 800
    assert row["status"] == "LOW"
    assert dashboard.json()["summary"]["low_stock_items"] == 1


def test_adjustment_requires_nonzero_signed_quantity():
    assert create_item().status_code == 200
    response = move(movement_type="ADJUSTMENT", quantity=0)
    assert response.status_code == 422

from fastapi.testclient import TestClient

from dairyos.app import app
from dairyos.data.database.session import SessionLocal
from dairyos.data.models.feed_inventory_item import FeedInventoryItem
from dairyos.data.models.inventory_transaction import InventoryTransaction


client = TestClient(app)


def _clean():
    session = SessionLocal()
    try:
        session.query(InventoryTransaction).delete(synchronize_session=False)
        session.query(FeedInventoryItem).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def setup_function():
    _clean()


def teardown_function():
    _clean()


def test_authoritative_projection_exposes_backend_owned_stock_metrics():
    item = client.post(
        "/farm/feed-inventory/items",
        json={"item": "Projection Maize", "category": "FEED", "unit": "kg", "active": True},
    )
    assert item.status_code == 200, item.text

    purchase = client.post(
        "/farm/feed-inventory/movements",
        json={"item": "Projection Maize", "movement_type": "PURCHASE", "quantity": 1000, "unit": "kg"},
    )
    assert purchase.status_code == 200, purchase.text

    consumption = client.post(
        "/farm/feed-inventory/movements",
        json={"item": "Projection Maize", "movement_type": "CONSUMPTION", "quantity": 250, "unit": "kg"},
    )
    assert consumption.status_code == 200, consumption.text

    response = client.get("/farm/feed-inventory/authoritative")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["frontend_calculation_authority"] is False
    row = body["items"][0]
    assert row["balance"] == 750
    assert row["used_from_operations"] == 250

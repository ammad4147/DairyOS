from __future__ import annotations


def test_feed_inventory_movement_persists_structured_finance_source(client):
    item = "Corn / Maize Silage"

    created_item = client.post(
        "/farm/feed-inventory/items",
        json={
            "item": item,
            "category": "FEED",
            "unit": "kg",
            "reorder_level": 0,
            "active": True,
        },
    )
    assert created_item.status_code == 200, created_item.text

    finance = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "FEED",
            "sub_category": item,
            "quantity": 100,
            "unit": "kg",
            "unit_rate": 50,
            "amount": 5000,
            "transaction_date": "2026-09-10",
            "payment_method": "CASH",
            "counterparty": "Traceability Supplier",
            "status": "PAID",
        },
    )
    assert finance.status_code == 200, finance.text
    finance_id = int(finance.json()["id"])

    movement = client.post(
        "/farm/feed-inventory/movements",
        json={
            "item": item,
            "movement_type": "ADJUSTMENT",
            "quantity": 10,
            "unit": "kg",
            "source_financial_transaction_id": finance_id,
            "notes": "Structured Finance linkage test",
        },
    )
    assert movement.status_code == 200, movement.text
    assert movement.json()["source_financial_transaction_id"] == finance_id

    listed = client.get(
        "/farm/feed-inventory/movements",
        params={"item": item},
    )
    assert listed.status_code == 200, listed.text
    rows = listed.json()["movements"]
    assert rows
    assert rows[0]["source_financial_transaction_id"] == finance_id


def test_feed_inventory_rejects_unknown_structured_finance_source(client):
    item = "Wheat Straw (Bhoosa)"

    created_item = client.post(
        "/farm/feed-inventory/items",
        json={
            "item": item,
            "category": "FEED",
            "unit": "kg",
            "reorder_level": 0,
            "active": True,
        },
    )
    assert created_item.status_code == 200, created_item.text

    movement = client.post(
        "/farm/feed-inventory/movements",
        json={
            "item": item,
            "movement_type": "ADJUSTMENT",
            "quantity": 10,
            "unit": "kg",
            "source_financial_transaction_id": 999999,
        },
    )
    assert movement.status_code == 422
    assert "not found" in movement.json()["detail"]

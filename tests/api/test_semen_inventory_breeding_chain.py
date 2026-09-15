from sqlalchemy.orm import Session

from dairyos.data.database.session import engine
from dairyos.data.models.semen_inventory import SemenStockMovement


def _purchase_semen(client):
    response = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Semen Straws (Sexed / Conventional)",
            "quantity": 5,
            "unit": "straw",
            "unit_rate": 4500,
            "amount": 22500,
            "transaction_date": "2026-09-06",
            "payment_method": "CASH",
            "counterparty": "Genetics Supplier",
            "status": "PAID",
            "semen_type": "SEXED",
            "sire_code": "SIRE-900",
            "bull_name": "Bull 900",
            "semen_breed": "Holstein",
            "semen_batch_number": "BATCH-900",
            "semen_storage_location": "Tank A",
            "semen_country_source": "Imported",
        },
    )
    assert response.status_code == 200, response.text
    stock = client.get("/farm/breeding/semen-stock")
    assert stock.status_code == 200, stock.text
    return next(row for row in stock.json()["available_lots"] if row["sire_code"] == "SIRE-900")


def test_finance_ledger_exposes_linked_semen_purchase_form_details(client):
    _purchase_semen(client)

    ledger = client.get("/farm/finance-ledger")
    assert ledger.status_code == 200, ledger.text
    row = next(
        item
        for item in ledger.json()["transactions"]
        if item["sub_category"] == "Semen Straws (Sexed / Conventional)"
    )

    assert row["quantity"] == 5
    assert row["unit"] == "straw"
    assert row["unit_rate"] == 4500
    assert row["semen_lot_code"].startswith("SEM-")
    assert row["semen_type"] == "SEXED"
    assert row["sire_code"] == "SIRE-900"
    assert row["bull_name"] == "Bull 900"
    assert row["semen_breed"] == "Holstein"
    assert row["semen_batch_number"] == "BATCH-900"
    assert row["semen_storage_location"] == "Tank A"
    assert row["semen_country_source"] == "Imported"
    assert row["semen_purchased_quantity"] == 5
    assert row["semen_unit_cost"] == 4500


def test_finance_semen_purchase_creates_selectable_stock_and_ai_consumes_one(client, registered_animal):
    lot = _purchase_semen(client)
    assert lot["available_straws"] == 5

    ai = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "insemination",
            "technician": "AI Tech",
            "operator": "AI Tech",
            "result": "RECORDED",
            "semen_lot_id": lot["id"],
            "timestamp": "2026-09-06",
        },
    )
    assert ai.status_code == 200, ai.text
    payload = ai.json()
    assert payload["semen_lot_id"] == lot["id"]
    assert payload["sire_code"] == "SIRE-900"
    assert payload["semen_supplier"] == "Genetics Supplier"

    stock_after = client.get("/farm/breeding/semen-stock").json()
    same = next(row for row in stock_after["lots"] if row["id"] == lot["id"])
    assert same["available_straws"] == 4

    with Session(engine) as session:
        movement = session.query(SemenStockMovement).filter_by(
            breeding_record_id=payload["record_id"]
        ).one()
        assert movement.signed_quantity == -1


def test_ai_requires_purchased_available_semen_lot(client, registered_animal):
    response = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "insemination",
            "technician": "AI Tech",
            "operator": "AI Tech",
            "result": "RECORDED",
            "timestamp": "2026-09-06",
        },
    )
    assert response.status_code == 422
    assert "available purchased semen lot" in response.text

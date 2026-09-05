from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from dairyos.data.database.session import engine
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.financial_transaction import FinancialTransaction


def seed_sale(client, animal_id):
    with Session(engine) as session, session.begin():
        session.add(MilkProduction(animal_id=animal_id, production_date=datetime(2026, 9, 1), total_yield=150, status="RECORDED"))
    response = client.post("/farm/finance-ledger", json={
        "transaction_type": "INCOME", "category": "MILK_SALES",
        "amount": 20000, "quantity": 100, "transaction_date": "2026-09-01",
        "counterparty": "Buyer", "status": "RECEIVABLE", "due_date": "2026-09-30",
    })
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_amendment_synchronizes_commercial_facts(client, registered_animal):
    transaction_id = seed_sale(client, registered_animal)
    response = client.patch(f"/farm/finance-ledger/{transaction_id}", json={"quantity": 110, "unit_rate": 200, "counterparty": "Revised Buyer"})
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        finance = session.get(FinancialTransaction, transaction_id)
        milk = session.query(MilkDisposition).filter_by(sale_id=f"FIN-{transaction_id}").one()
        assert finance.amount == milk.amount_due == Decimal("22000.00")
        assert finance.quantity == milk.quantity_litres == 110
        assert finance.unit_rate == milk.selling_price_per_litre == Decimal("200")
        assert finance.counterparty == milk.counterparty == "Revised Buyer"
        disposition_id = milk.id
    response = client.patch(
        f"/farm/milk/dispositions/{disposition_id}",
        json={"quantity_litres": 120},
    )
    assert response.status_code == 200, response.text

    with Session(engine) as session:
        finance = session.get(FinancialTransaction, transaction_id)
        milk = (
            session.query(MilkDisposition)
            .filter_by(sale_id=f"FIN-{transaction_id}")
            .one()
        )
        assert finance.quantity == milk.quantity_litres == 120
        assert finance.unit_rate == milk.selling_price_per_litre == Decimal("200.000000")
        assert finance.amount == milk.amount_due == Decimal("24000.00")


def test_failed_amendment_preserves_both_ledgers(client, registered_animal, monkeypatch):
    from dairyos.api import finance_ledger

    transaction_id = seed_sale(client, registered_animal)

    def fail(**kwargs):
        raise RuntimeError("injected projection failure")

    monkeypatch.setattr(finance_ledger, "_sync_existing_milk_sale_status", fail)
    import pytest
    with pytest.raises(RuntimeError, match="injected projection failure"):
        client.patch(f"/farm/finance-ledger/{transaction_id}", json={"amount": 22000})
    with Session(engine) as session:
        finance = session.get(FinancialTransaction, transaction_id)
        milk = session.query(MilkDisposition).filter_by(sale_id=f"FIN-{transaction_id}").one()
        assert finance.amount == milk.amount_due == Decimal("20000.00")

"""Remediation: a receipt must not be posted against a Finance-originated sale.

Defect (found during the Reporting redesign, 2026-09-18). ``POST
/farm/milk/sales/{sale_id}/receipt`` posts a ``RECEIPT`` Finance transaction.
The canonical classifier counts ``RECEIPT`` as revenue. For a sale created
on the Milk tab that receipt *is* the revenue, which is correct. For a sale
created in Finance (``sale_id = FIN-{transaction}``) the primary ``INCOME``
transaction is already the revenue, so the receipt counted the same money a
second time, and it moved ``MilkDisposition.amount_received`` while the
primary Finance transaction stayed RECEIVABLE, breaking the documented milk
sale consistency invariant (DAIRYOS_DATA_AUTHORITY_REGISTER.md).

Authority affected: Finance revenue (``transaction_classifier.is_income``)
and every consumer of it: Finance tab, Dashboard, profitability, Reporting.
"""

from datetime import date
from decimal import Decimal

from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.milk_production import MilkProduction
from dairyos.finance.classification import transaction_classifier as classifier
from tests import conftest as root

DAY = date(2026, 9, 1)


def _seed(session):
    from dairyos.data.models.animal import Animal
    from datetime import datetime

    session.add(Animal(animal_id="RG-001", animal_type="CATTLE", sex="FEMALE", lifecycle_status="LACTATING",
                       status="ACTIVE", active=True, is_currently_milking=True))
    session.flush()
    session.add(MilkProduction(animal_id="RG-001", production_date=datetime(2026, 9, 1, 6), session_ledger=True,
                               morning_yield=500.0, total_yield=500.0, status="RECORDED"))
    sale = FinancialTransaction(transaction_type="INCOME", category="MILK_SALES", amount=Decimal("100000"),
                                transaction_date=datetime(2026, 9, 1), status="RECEIVABLE", quantity=400.0,
                                unit="litre", unit_rate=Decimal("250"), currency="PKR")
    session.add(sale)
    session.flush()
    session.add(MilkDisposition(production_date=DAY, disposition_type="SOLD", quantity_litres=400.0,
                                sale_id=f"FIN-{sale.id}", selling_price_per_litre=Decimal("250"),
                                amount_due=Decimal("100000"), amount_received=Decimal("0"), status="RECORDED"))
    session.add(MilkDisposition(production_date=DAY, disposition_type="SOLD", quantity_litres=50.0,
                                sale_id="MILK-TAB-1", selling_price_per_litre=Decimal("200"),
                                amount_due=Decimal("10000"), amount_received=Decimal("0"), status="RECORDED"))
    session.commit()
    return sale.id


def _revenue(session) -> Decimal:
    session.expire_all()
    return sum((Decimal(str(row.amount)) for row in session.query(FinancialTransaction).all()
                if classifier.is_income(row)), Decimal("0"))


def test_receipt_against_finance_originated_sale_is_refused(client):
    session = root.container.repository_factory.session
    sale_id = _seed(session)
    assert _revenue(session) == Decimal("100000.00")

    response = client.post(f"/farm/milk/sales/FIN-{sale_id}/receipt", json={"amount": "100000"})

    assert response.status_code == 409, response.text
    assert "Finance" in response.json()["detail"]
    assert _revenue(session) == Decimal("100000.00"), "the sale must not be counted twice"
    disposition = session.query(MilkDisposition).filter(MilkDisposition.sale_id == f"FIN-{sale_id}").one()
    assert Decimal(str(disposition.amount_received)) == Decimal("0.00")


def test_receipt_against_milk_tab_sale_still_works(client):
    session = root.container.repository_factory.session
    _seed(session)

    response = client.post("/farm/milk/sales/MILK-TAB-1/receipt", json={"amount": "4000", "received_on": "2026-09-02"})

    assert response.status_code == 200, response.text
    assert Decimal(str(response.json()["receivable_outstanding"])) == Decimal("6000.00")
    assert _revenue(session) == Decimal("104000.00")

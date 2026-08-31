"""Operator-surface simulation for herd strength and credit receivables.

The scenarios use the public APIs and then inspect the main Dashboard contract.
They are intentionally strict: inactive animals remain historically queryable,
but cannot contribute to active herd strength; credit revenue remains a
receivable until it is settled.
"""

from __future__ import annotations


def _register(client, tag: str) -> str:
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "ear_tag": tag,
            "breed": "HF",
            "sex": "FEMALE",
            "lifecycle_status": "HEIFER",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _dashboard(client):
    response = client.get("/dashboard")
    assert response.status_code == 200, response.text
    return response.json()


def _find_numeric_by_key(value, needle: str):
    if isinstance(value, dict):
        for key, child in value.items():
            if needle in str(key).lower() and isinstance(child, (int, float)):
                yield float(child)
            yield from _find_numeric_by_key(child, needle)
    elif isinstance(value, list):
        for child in value:
            yield from _find_numeric_by_key(child, needle)


def test_sale_and_mortality_reduce_active_herd_but_preserve_passports(client):
    sold_id = _register(client, "SIM-DASH-SOLD-001")
    deceased_id = _register(client, "SIM-DASH-DECEASED-001")

    before_active = {row["animal_id"] for row in client.get("/farm/animals?active_only=true").json()}
    assert {sold_id, deceased_id}.issubset(before_active)

    sold = client.patch(
        f"/farm/animals/{sold_id}/disposition",
        json={
            "disposition": "SOLD",
            "effective_date": "2026-08-30",
            "reason": "Dashboard disposition simulation",
            "buyer_or_counterparty": "Simulation Buyer",
            "amount": 250000,
            "operator": "simulation",
        },
    )
    assert sold.status_code == 200, sold.text

    deceased = client.patch(
        f"/farm/animals/{deceased_id}/disposition",
        json={
            "disposition": "DECEASED",
            "effective_date": "2026-08-30",
            "cause": "Dashboard mortality simulation",
            "veterinarian": "simulation",
            "operator": "simulation",
        },
    )
    assert deceased.status_code == 200, deceased.text

    after_active = {row["animal_id"] for row in client.get("/farm/animals?active_only=true").json()}
    assert sold_id not in after_active
    assert deceased_id not in after_active

    sold_passport = client.get(f"/farm/animals/{sold_id}/passport")
    deceased_passport = client.get(f"/farm/animals/{deceased_id}/passport")
    assert sold_passport.status_code == 200, sold_passport.text
    assert deceased_passport.status_code == 200, deceased_passport.text
    assert sold_passport.json()["animal"]["active"] is False
    assert deceased_passport.json()["animal"]["active"] is False
    assert sold_passport.json()["animal"]["status"] == "SOLD"
    assert deceased_passport.json()["animal"]["status"] == "DECEASED"

    dashboard = _dashboard(client)
    # Dashboard exposes its authoritative current herd strength explicitly;
    # do not infer it from unrelated numeric fields such as milking counts.
    assert dashboard["animals"]["total"] == len(after_active), dashboard
    assert dashboard["dashboard"]["animals"]["total"] == len(after_active), dashboard


def test_credit_milk_sale_appears_as_receivable_on_finance_and_main_dashboard_then_settles(client):
    sale = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "INCOME",
            "category": "MILK_SALES",
            "quantity": 20,
            "amount": 4500,
            "transaction_date": "2026-08-30",
            "payment_method": "CREDIT",
            "counterparty": "Simulation Milk Buyer",
            "reference": "SIM-CREDIT-MILK-002",
            "notes": "20 L milk at PKR 225/L sold on credit",
            "status": "RECEIVABLE",
            "due_date": "2026-09-15",
        },
    )
    assert sale.status_code == 200, sale.text
    transaction_id = sale.json()["id"]

    finance = client.get("/farm/finance-ledger")
    assert finance.status_code == 200, finance.text
    matching = [row for row in finance.json()["transactions"] if row["id"] == transaction_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "RECEIVABLE"
    assert matching[0]["amount"] == 4500.0

    dashboard_before = _dashboard(client)
    assert dashboard_before["finance"]["receivables"] >= 4500.0, dashboard_before
    assert dashboard_before["dashboard"]["finance"]["receivables"] >= 4500.0, dashboard_before

    received = client.post(
        f"/farm/finance-ledger/{transaction_id}/status",
        json={
            "status": "RECEIVED",
            "reason": "Simulation customer payment received",
        },
    )
    assert received.status_code == 200, received.text
    assert received.json()["status"] == "RECEIVED"
    assert received.json()["settled_date"] is not None

    finance_after = client.get("/farm/finance-ledger")
    assert finance_after.status_code == 200, finance_after.text
    settled = [row for row in finance_after.json()["transactions"] if row["id"] == transaction_id]
    assert len(settled) == 1
    assert settled[0]["status"] == "RECEIVED"
    assert settled[0]["amount"] == 4500.0

    dashboard_after = _dashboard(client)
    assert dashboard_after["finance"]["receivables"] == 0.0, dashboard_after
    assert dashboard_after["dashboard"]["finance"]["receivables"] == 0.0, dashboard_after

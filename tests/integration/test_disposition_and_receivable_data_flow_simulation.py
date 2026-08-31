"""Input-driven disposition and credit-revenue data-flow simulations.

These scenarios use public API entry points and reconcile persisted facts across
Animal Passport, active-herd strength, Finance, and the main Dashboard.
"""

from __future__ import annotations


def _register(client, *, tag: str, lifecycle: str = "HEIFER") -> str:
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "ear_tag": tag,
            "breed": "HF",
            "sex": "FEMALE",
            "lifecycle_status": lifecycle,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _active_animals(client):
    response = client.get("/farm/animals", params={"active_only": "true"})
    assert response.status_code == 200, response.text
    return response.json()


def _all_animals(client):
    response = client.get("/farm/animals", params={"active_only": "false"})
    assert response.status_code == 200, response.text
    return response.json()


def _passport(client, animal_id: str):
    response = client.get(f"/farm/animals/{animal_id}/passport")
    assert response.status_code == 200, response.text
    return response.json()


def test_sold_and_mortality_leave_passports_but_leave_active_herd_strength(client):
    sold_id = _register(client, tag="SIM-SOLD-001")
    mortality_id = _register(client, tag="SIM-DECEASED-001")

    baseline_active_ids = {row["animal_id"] for row in _active_animals(client)}
    baseline_all_ids = {row["animal_id"] for row in _all_animals(client)}
    assert {sold_id, mortality_id}.issubset(baseline_active_ids)

    sold = client.patch(
        f"/farm/animals/{sold_id}/disposition",
        json={
            "disposition": "SOLD",
            "effective_date": "2026-08-30",
            "reason": "Input-driven sale simulation",
            "buyer_or_counterparty": "Simulation Buyer",
            "amount": 250000,
            "reference": "SIM-SALE-001",
            "operator": "simulation",
        },
    )
    assert sold.status_code == 200, sold.text

    deceased = client.patch(
        f"/farm/animals/{mortality_id}/disposition",
        json={
            "disposition": "DECEASED",
            "effective_date": "2026-08-30",
            "cause": "Input-driven mortality simulation",
            "veterinarian": "simulation",
            "operator": "simulation",
        },
    )
    assert deceased.status_code == 200, deceased.text

    active_ids = {row["animal_id"] for row in _active_animals(client)}
    all_ids = {row["animal_id"] for row in _all_animals(client)}
    assert sold_id not in active_ids
    assert mortality_id not in active_ids
    assert baseline_active_ids - {sold_id, mortality_id} <= active_ids
    assert baseline_all_ids | {sold_id, mortality_id} <= all_ids

    sold_passport = _passport(client, sold_id)
    deceased_passport = _passport(client, mortality_id)
    assert sold_passport["animal"]["active"] is False
    assert sold_passport["animal"]["status"] == "SOLD"
    assert deceased_passport["animal"]["active"] is False
    assert deceased_passport["animal"]["status"] == "DECEASED"
    assert sold_passport["animal"]["animal_id"] == sold_id
    assert deceased_passport["animal"]["animal_id"] == mortality_id


def _recursive_values(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _recursive_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _recursive_values(child)


def test_credit_milk_sale_becomes_receivable_then_is_received_in_same_ledger_and_dashboard(client):
    sale = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "INCOME",
            "category": "MILK_SALES",
            "quantity": 10,
            "amount": 2250,
            "transaction_date": "2026-08-30",
            "payment_method": "CREDIT",
            "counterparty": "Simulation Dairy Buyer",
            "reference": "SIM-MILK-CREDIT-001",
            "notes": "10 L milk sold on credit at PKR 225/L",
            "status": "RECEIVABLE",
            "due_date": "2026-09-15",
        },
    )
    assert sale.status_code == 200, sale.text
    created = sale.json()
    transaction_id = created["id"]
    assert created["status"] == "RECEIVABLE"
    assert created["amount"] == 2250.0
    assert created["due_date"] == "2026-09-15"

    ledger = client.get("/farm/finance-ledger")
    assert ledger.status_code == 200, ledger.text
    rows = [
        row for row in ledger.json()["transactions"]
        if row["id"] == transaction_id
    ]
    assert len(rows) == 1, rows
    assert rows[0]["status"] == "RECEIVABLE"
    assert rows[0]["transaction_type"] == "INCOME"
    assert rows[0]["category"] == "MILK_SALES"
    assert rows[0]["amount"] == 2250.0

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    dashboard_body = dashboard.json()
    receivable_amounts = [
        child
        for key, child in _recursive_values(dashboard_body)
        if "receivable" in str(key).lower() and isinstance(child, (int, float))
    ]
    assert 2250.0 in receivable_amounts, dashboard_body

    received = client.post(
        f"/farm/finance-ledger/{transaction_id}/status",
        json={
            "status": "RECEIVED",
            "reason": "Customer payment received",
        },
    )
    assert received.status_code == 200, received.text
    received_row = received.json()
    assert received_row["status"] == "RECEIVED"
    assert received_row["settled_date"] is not None

    ledger_after = client.get("/farm/finance-ledger")
    assert ledger_after.status_code == 200, ledger_after.text
    rows_after = [
        row for row in ledger_after.json()["transactions"]
        if row["id"] == transaction_id
    ]
    assert len(rows_after) == 1, rows_after
    assert rows_after[0]["status"] == "RECEIVED"
    assert rows_after[0]["amount"] == 2250.0

    dashboard_after = client.get("/dashboard")
    assert dashboard_after.status_code == 200, dashboard_after.text
    dashboard_after_body = dashboard_after.json()
    receivable_after = [
        child
        for key, child in _recursive_values(dashboard_after_body)
        if "receivable" in str(key).lower() and isinstance(child, (int, float))
    ]
    assert 2250.0 not in receivable_after, dashboard_after_body

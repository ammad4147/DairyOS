"""Finance financing and livestock-capital workflow contracts."""

from dairyos.finance.classification import transaction_classifier as classifier


def _owner_investment_payload(**overrides):
    payload = {
        "transaction_type": "OWNER_INVESTMENT",
        "category": "OWNER_INVESTMENT",
        "amount": 100000.0,
        "payment_method": "BANK",
        "status": "RECEIVED",
        "counterparty": "Owner",
        "notes": "Initial working capital",
    }
    payload.update(overrides)
    return payload


def _animal_purchase_payload(**overrides):
    payload = {
        "transaction_type": "EXPENSE",
        "master_category": "OPEX",
        "sub_category": "Animal Purchase",
        "animal_category": "Milking",
        "amount": 1500000.0,
        "payment_method": "BANK",
        "status": "PAID",
        "counterparty": "Livestock Supplier",
        "transaction_date": "2026-09-12",
    }
    payload.update(overrides)
    return payload


def test_owner_investment_is_financing_cash_not_operating_revenue(client):
    response = client.post(
        "/farm/finance-ledger",
        json=_owner_investment_payload(),
    )

    assert response.status_code == 200, response.text
    row = response.json()
    assert row["transaction_type"] == "OWNER_INVESTMENT"
    assert row["category"] == "OWNER_INVESTMENT"
    assert row["status"] == "RECEIVED"
    assert classifier.is_cash_inflow_only(type("Row", (), row)())
    assert not classifier.is_income(type("Row", (), row)())

    reconciliation = client.get(
        "/farm/finance/reconciliation?period=yearly"
    )
    assert reconciliation.status_code == 200, reconciliation.text
    summary = reconciliation.json()
    assert summary["income"] == 0.0
    assert summary["capital_inflows"] == 100000.0
    assert summary["expenses"] == 0.0
    assert summary["net_movement"] == 0.0
    assert summary["net_cash_movement"] == 100000.0

    cop = client.get("/farm/finance/cost-of-production?days=30")
    assert cop.status_code == 200, cop.text
    assert cop.json()["total_operating_cost"] == 0.0


def test_owner_investment_requires_its_financing_contract(client):
    invalid_category = client.post(
        "/farm/finance-ledger",
        json=_owner_investment_payload(category="OTHER_REVENUE"),
    )
    assert invalid_category.status_code == 422, invalid_category.text

    expense_details = client.post(
        "/farm/finance-ledger",
        json=_owner_investment_payload(quantity=1, unit="head"),
    )
    assert expense_details.status_code == 422, expense_details.text


def test_compatibility_finance_route_governs_owner_investment(client):
    response = client.post(
        "/farm/financial",
        json={
            "transaction_type": "OWNER_INVESTMENT",
            "category": "OWNER_INVESTMENT",
            "amount": 25000.0,
            "payment_method": "CASH",
            "operator": "Owner",
        },
    )

    assert response.status_code == 200, response.text
    row = response.json()
    assert row["transaction_type"] == "OWNER_INVESTMENT"
    assert row["category"] == "OWNER_INVESTMENT"
    assert row["status"] == "RECEIVED"


def test_animal_purchase_persists_standard_category_and_is_non_opex(client):
    response = client.post(
        "/farm/finance-ledger",
        json=_animal_purchase_payload(),
    )

    assert response.status_code == 200, response.text
    row = response.json()
    assert row["sub_category"] == "Animal Purchase"
    assert row["category"] == "ANIMAL_PURCHASE"
    assert row["animal_category"] == "Milking"
    assert row["animal_id"] is None
    assert row["cop_classification"] == "NON_OPEX"
    assert row["cop_attribution_method"] is None

    taxonomy = client.get("/farm/finance-ledger/taxonomy")
    assert taxonomy.status_code == 200, taxonomy.text
    categories = taxonomy.json()["animal_purchase_categories"]
    assert [item["value"] for item in categories] == [
        "Milking",
        "Dry",
        "Heifer",
        "Female Calf",
        "Male Calf",
        "Bull",
    ]

    cop = client.get("/farm/finance/cost-of-production?days=30")
    assert cop.status_code == 200, cop.text
    cop_body = cop.json()
    assert cop_body["total_operating_cost"] == 0.0
    assert cop_body["total_recorded_operating_expense"] == 0.0
    assert cop_body["non_opex_excluded"] == 1500000.0

    reconciliation = client.get(
        "/farm/finance/reconciliation?period=yearly"
    ).json()
    assert reconciliation["expenses"] == 1500000.0
    assert reconciliation["opex"] == 0.0
    assert reconciliation["total_operating_cost"] == 0.0


def test_animal_purchase_link_is_category_checked_and_idempotent(
    client,
    registered_animal,
):
    purchase = client.post(
        "/farm/finance-ledger",
        json=_animal_purchase_payload(),
    )
    assert purchase.status_code == 200, purchase.text
    transaction_id = purchase.json()["id"]

    linked = client.post(
        f"/farm/finance-ledger/{transaction_id}/link-animal",
        json={"animal_id": registered_animal},
    )
    assert linked.status_code == 200, linked.text
    linked_body = linked.json()
    assert linked_body["animal_id"] == registered_animal
    assert "ANIMAL_PURCHASE_LINKED_AT=" in linked_body["notes"]

    repeated = client.post(
        f"/farm/finance-ledger/{transaction_id}/link-animal",
        json={"animal_id": registered_animal},
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["animal_id"] == registered_animal


def test_animal_purchase_cannot_link_to_a_different_standard_category(
    client,
    registered_animal,
):
    purchase = client.post(
        "/farm/finance-ledger",
        json=_animal_purchase_payload(animal_category="Dry"),
    )
    assert purchase.status_code == 200, purchase.text

    response = client.post(
        f"/farm/finance-ledger/{purchase.json()['id']}/link-animal",
        json={"animal_id": registered_animal},
    )
    assert response.status_code == 409, response.text
    assert "does not match" in response.json()["detail"]

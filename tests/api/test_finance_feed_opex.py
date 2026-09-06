from dairyos.finance.expense_taxonomy import EXPENSE_TAXONOMIES, MASTER_CATEGORIES, all_items, legacy_category


def test_feed_and_opex_taxonomy_is_unique_and_contains_other():
    assert MASTER_CATEGORIES == {"FEED", "OPEX"}
    for master, groups in EXPENSE_TAXONOMIES.items():
        items = [item for values in groups.values() for item in values]
        assert len(items) == len(set(items)), master
        assert "Other" in items


def test_legacy_mapping_keeps_existing_cost_domains():
    assert legacy_category("FEED", "Corn / Maize Silage") == "FEED"
    assert legacy_category("OPEX", "Routine Vet Fees / Consultation") == "HEALTH"
    assert legacy_category("OPEX", "Semen Straws (Sexed / Conventional)") == "BREEDING"
    assert legacy_category("OPEX", "Milker Wages") == "LABOUR"
    assert legacy_category("OPEX", "Grid Electricity (WAPDA)") == "UTILITIES"


def test_taxonomy_endpoint_is_governed(client):
    body = client.get("/farm/finance-ledger/taxonomy")
    assert body.status_code == 200, body.text
    data = body.json()
    assert set(data["master_categories"]) == {"FEED", "OPEX"}
    assert "Corn / Maize Silage" in data["items"]["FEED"]
    assert "Routine Vet Fees / Consultation" in data["items"]["OPEX"]
    assert "Other" in data["items"]["FEED"]
    assert "Other" in data["items"]["OPEX"]


def _post_expense(client, **overrides):
    payload = {
        "transaction_type": "EXPENSE",
        "master_category": "FEED",
        "sub_category": "Corn / Maize Silage",
        "quantity": 500,
        "unit": "kg",
        "unit_rate": 18,
        "transaction_date": "2026-08-22",
        "payment_method": "BANK",
        "counterparty": "ABC Feed Supplier",
        "reference": "BILL-001",
        "notes": "Silage batch",
    }
    payload.update(overrides)
    return client.post("/farm/finance-ledger", json=payload)


def test_feed_entry_is_persisted_as_feed_with_calculated_amount(client):
    response = _post_expense(client)
    assert response.status_code == 200, response.text
    row = response.json()
    assert row["master_category"] == "FEED"
    assert row["sub_category"] == "Corn / Maize Silage"
    assert row["quantity"] == 500
    assert row["unit_rate"] == 18
    assert row["amount"] == 9000
    assert row["vendor_name"] == "ABC Feed Supplier"
    assert row["payment_method"] == "BANK"

    ledger = client.get("/farm/finance-ledger").json()["transactions"]
    stored = next(item for item in ledger if item["id"] == row["id"])
    assert stored["amount"] == 9000


def test_opex_entry_is_persisted_in_same_ledger(client):
    response = _post_expense(
        client,
        master_category="OPEX",
        sub_category="Routine Vet Fees / Consultation",
        quantity=1,
        unit="service",
        unit_rate=5000,
        payment_method="CASH",
    )
    assert response.status_code == 200, response.text
    row = response.json()
    assert row["master_category"] == "OPEX"
    assert row["category"] == "HEALTH"

    ledger = client.get("/farm/finance-ledger").json()["transactions"]
    rows = [item for item in ledger if item["master_category"] in {"FEED", "OPEX"}]
    assert len(rows) == 1


def test_other_requires_custom_specification(client):
    response = _post_expense(client, sub_category="Other", custom_specification=None)
    assert response.status_code == 422, response.text

    response = _post_expense(
        client,
        master_category="OPEX",
        sub_category="Other",
        custom_specification="Pest-control service",
        quantity=None,
        unit=None,
        unit_rate=None,
        amount=3500,
        cop_classification="OPEX",
        cop_attribution_method="DIRECT",
        cop_service_date="2026-08-22",
    )
    assert response.status_code == 200, response.text
    row = response.json()
    assert row["custom_specification"] == "Pest-control service"
    assert row["master_category"] == "OPEX"


def test_other_cannot_carry_custom_specification_for_normal_item(client):
    response = _post_expense(client, custom_specification="Should not be accepted")
    assert response.status_code == 422, response.text


def test_feed_opex_cost_endpoint_splits_same_persistent_ledger(client, registered_animal):
    milk = client.post(
        "/farm/milk",
        json={"animal_id": registered_animal, "morning_yield": 100.0, "operator": "Test"},
    )
    assert milk.status_code == 200, milk.text

    assert _post_expense(client, quantity=100, unit="kg", unit_rate=10).status_code == 200
    assert _post_expense(
        client,
        master_category="OPEX",
        sub_category="Grid Electricity (WAPDA)",
        quantity=1,
        unit="bill",
        unit_rate=500,
        cop_classification="OPEX",
        cop_attribution_method="PERIODIC",
        cop_coverage_start="2026-08-22",
        cop_coverage_end="2026-08-22",
    ).status_code == 200

    body = client.get("/farm/finance-ledger/cost-of-production?days=30")
    assert body.status_code == 200, body.text
    data = body.json()
    assert data["feed_cost"] == 1000
    assert data["opex"] == 500
    assert data["unattributed_opex"] == 0
    assert data["total_operating_cost"] == 1500
    assert data["cmpl"] == 15
    assert data["feed_cost_per_litre"] == 10
    assert data["opex_cost_per_litre"] == 5


def test_voided_transaction_is_not_counted_in_feed_or_opex(client):
    response = _post_expense(client, quantity=100, unit="kg", unit_rate=10)
    assert response.status_code == 200, response.text
    transaction = response.json()

    voided = client.post(
        f"/farm/finance-ledger/{transaction['id']}/status",
        json={"status": "VOID", "reason": "Testing void"},
    )
    assert voided.status_code == 200, voided.text

    body = client.get("/farm/finance-ledger/cost-of-production?days=30").json()
    assert body["feed_cost"] == 0
    assert body["total_operating_cost"] == 0

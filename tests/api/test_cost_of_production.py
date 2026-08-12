from datetime import datetime


def test_cost_of_production_reads_persisted_milk_and_finance(client, registered_animal):
    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 10.0,
            "operator": "Milking Operator",
        },
    )
    assert milk.status_code == 200, milk.text

    feed_cost = client.post(
        "/farm/financial",
        json={
            "transaction_type": "EXPENSE",
            "amount": 1200.0,
            "category": "FEED",
            "operator": "Farm Manager",
        },
    )
    assert feed_cost.status_code == 200, feed_cost.text

    veterinary_cost = client.post(
        "/farm/financial",
        json={
            "transaction_type": "EXPENSE",
            "amount": 300.0,
            "category": "VETERINARY",
            "operator": "Farm Manager",
        },
    )
    assert veterinary_cost.status_code == 200, veterinary_cost.text

    milk_sale = client.post(
        "/farm/financial",
        json={
            "transaction_type": "INCOME",
            "amount": 750.0,
            "category": "MILK SALE",
            "operator": "Farm Manager",
        },
    )
    assert milk_sale.status_code == 200, milk_sale.text

    response = client.get("/farm/finance/cost-of-production?days=30")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["milk_litres"] >= 10.0
    assert body["total_recorded_operating_expense"] >= 1500.0
    assert body["cost_per_litre"] == 150.0
    assert body["expense_by_category"]["FEED"] >= 1200.0
    assert body["expense_by_category"]["VETERINARY"] >= 300.0
    assert body["milk_revenue"] >= 750.0
    assert body["revenue_per_litre"] == 75.0
    assert body["margin_after_recorded_operating_cost"] == -750.0


def test_cost_of_production_does_not_invent_metrics_without_persisted_inputs(client):
    response = client.get("/farm/finance/cost-of-production?days=30")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["milk_litres"] == 0.0
    assert body["cost_per_litre"] is None
    assert body["revenue_per_litre"] is None
    assert body["margin_after_recorded_operating_cost"] is None

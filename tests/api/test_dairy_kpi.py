def test_standard_dairy_kpis_read_persisted_operational_records(client, registered_animal):
    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "afternoon_yield": 7.0,
            "operator": "Milking Operator",
        },
    )
    assert milk.status_code == 200, milk.text

    feed = client.post(
        "/farm/feed/records",
        json={
            "animal_id": registered_animal,
            "feed_type": "SILAGE",
            "quantity_kg": 20.0,
            "notes": "KPI test ration",
        },
    )
    assert feed.status_code == 200, feed.text

    health = client.post(
        "/farm/health-observations",
        json={
            "animal_id": registered_animal,
            "symptom": "Lethargy",
            "severity": "ELEVATED",
            "operator": "Dr Vet",
        },
    )
    assert health.status_code == 200, health.text

    response = client.get("/farm/kpis/overview?days=30")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["methodology"]["synthetic_values"] is False
    assert body["record_counts"]["milk"] >= 1
    assert body["record_counts"]["feed"] >= 1
    assert body["record_counts"]["health"] >= 1
    assert body["kpis"]["milk_production_liters"] == 15.0
    assert body["kpis"]["feed_consumption_kg"] == 20.0
    assert body["kpis"]["feed_kg_per_liter_milk"] is None
    assert body["coverage"]["missing_metrics"]
    assert body["coverage"]["definitions"]["feed_conversion"].startswith("not calculated")
    assert body["kpis"]["average_milk_liters_per_animal_day"] == 15.0


def test_standard_dairy_kpis_do_not_invent_derived_metrics_without_inputs(client, registered_animal):
    response = client.get("/farm/kpis/overview?days=30")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["data_status"] == "NO_DATA"
    assert body["record_counts"]["milk"] == 0
    assert body["record_counts"]["feed"] == 0
    assert body["record_counts"]["health"] == 0
    assert body["kpis"]["milk_production_liters"] is None
    assert body["kpis"]["feed_consumption_kg"] is None
    assert body["kpis"]["feed_kg_per_liter_milk"] is None
    assert body["kpis"]["average_milk_liters_per_animal_day"] is None
    assert body["methodology"]["synthetic_values"] is False


def test_standard_dairy_kpis_support_explicit_period(client):
    response = client.get(
        "/farm/kpis/period?start_date=2026-08-01&end_date=2026-08-12"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["period"]["start"].startswith("2026-08-01")
    assert body["period"]["end"].startswith("2026-08-13")
    assert body["data_status"] == "NO_DATA"

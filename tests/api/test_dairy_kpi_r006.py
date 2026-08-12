def test_r006_kpi_engine_reports_standard_coverage_and_peak_milk(client, registered_animal):
    first = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "afternoon_yield": 7.0,
            "operator": "KPI Operator",
        },
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 6.0,
            "afternoon_yield": 5.0,
            "operator": "KPI Operator",
        },
    )
    assert second.status_code == 200, second.text

    response = client.get("/farm/kpis/overview?days=30")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["kpis"]["peak_daily_milk_liters"] == 26.0
    assert "peak_daily_milk" in body["coverage"]["complete_metrics"]
    assert "persistency" in body["coverage"]["missing_metrics"]
    assert "mortality_rate" in body["coverage"]["missing_metrics"]
    assert body["methodology"]["synthetic_values"] is False

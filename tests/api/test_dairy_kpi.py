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

def test_feed_kpi_interprets_naive_feeding_date_in_farm_timezone():
    from datetime import UTC, datetime
    from zoneinfo import ZoneInfo

    from dairyos.api.dairy_kpi import _as_farm_local_datetime

    farm_timezone = ZoneInfo("Asia/Karachi")
    stored = datetime(2026, 9, 13, 19, 43, 44)

    converted = _as_farm_local_datetime(stored, farm_timezone)

    assert converted == datetime(2026, 9, 13, 14, 43, 44, tzinfo=UTC)


def test_feed_kpi_local_day_boundary_is_half_open():
    from datetime import UTC, datetime
    from zoneinfo import ZoneInfo

    from dairyos.api.dairy_kpi import _as_farm_local_datetime

    farm_timezone = ZoneInfo("Asia/Karachi")
    start = datetime(2026, 9, 12, 19, 0, tzinfo=UTC)
    end = datetime(2026, 9, 13, 19, 0, tzinfo=UTC)

    before_midnight = _as_farm_local_datetime(
        datetime(2026, 9, 13, 23, 59, 59),
        farm_timezone,
    )
    next_midnight = _as_farm_local_datetime(
        datetime(2026, 9, 14, 0, 0, 0),
        farm_timezone,
    )

    assert start <= before_midnight < end
    assert not (start <= next_midnight < end)


def test_feed_kpi_preserves_aware_timestamp_instant():
    from datetime import UTC, datetime, timedelta, timezone

    from dairyos.api.dairy_kpi import _as_farm_local_datetime

    supplied = datetime(
        2026,
        9,
        13,
        19,
        43,
        44,
        tzinfo=timezone(timedelta(hours=5)),
    )

    converted = _as_farm_local_datetime(supplied, UTC)

    assert converted == datetime(2026, 9, 13, 14, 43, 44, tzinfo=UTC)


def test_generic_kpi_naive_datetime_contract_remains_utc():
    from datetime import UTC, datetime
    from zoneinfo import ZoneInfo

    from dairyos.api.dairy_kpi import _as_datetime, _as_farm_local_datetime

    naive = datetime(2026, 9, 13, 19, 43, 44)

    assert _as_datetime(naive) == naive.replace(tzinfo=UTC)
    assert _as_farm_local_datetime(
        naive,
        ZoneInfo("Asia/Karachi"),
    ) == datetime(2026, 9, 13, 14, 43, 44, tzinfo=UTC)

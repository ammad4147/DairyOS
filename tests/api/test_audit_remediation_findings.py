"""Regression coverage for the confirmed findings in the interim audit."""

from datetime import datetime, time, timedelta

from dairyos.api.tmr import DAILY_COST_SNAPSHOT_GROUP, lock_daily_tmr_cost_snapshot
from dairyos.app import container
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.data.models.milk_production_correction import (
    MilkProductionCorrection,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


def _farm_day():
    return OperationalDateAuthority(
        repository_factory=container.repository_factory,
    ).current_date()


def _record_session(client, animal_id, production_date, session, litres):
    fields = {
        "MORNING": "morning_yield",
        "AFTERNOON": "afternoon_yield",
        "EVENING": "evening_yield",
    }
    return client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "milking_session": session,
            "production_date": production_date.isoformat(),
            fields[session]: litres,
            "operator": "Audit Regression",
        },
    )


def test_named_milk_session_cannot_carry_other_session_yields(
    client,
    registered_animal,
):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 10,
            "afternoon_yield": 8,
        },
    )

    assert response.status_code == 422, response.text
    assert container.repository_factory.milk().get_all() == []
    assert container.repository_factory.milking_session_ledger().get_all() == []


def test_not_milked_session_cannot_coexist_with_animal_production(
    client,
    registered_animal,
):
    day = _farm_day()
    declared = client.post(
        "/farm/milk/not-milked",
        json={
            "milking_session": "MORNING",
            "operational_date": day.isoformat(),
            "reason": "POWER_OUTAGE",
        },
    )
    assert declared.status_code == 200, declared.text

    production = _record_session(
        client,
        registered_animal,
        day,
        "MORNING",
        12,
    )

    assert production.status_code == 409, production.text
    assert production.json()["detail"]["error"] == (
        "MILKING_SESSION_ALREADY_NOT_MILKED"
    )
    assert container.repository_factory.milk().get_all() == []


def test_milk_correction_requires_reason_and_keeps_before_after_history(
    client,
    registered_animal,
):
    day = _farm_day() - timedelta(days=2)
    for session, litres in (
        ("MORNING", 10),
        ("AFTERNOON", 8),
        ("EVENING", 7),
    ):
        response = _record_session(
            client,
            registered_animal,
            day,
            session,
            litres,
        )
        assert response.status_code == 200, response.text

    row = client.get(
        "/farm/milk/ledger",
        params={"start_date": day, "end_date": day},
    ).json()["production"][0]

    rejected = client.patch(
        f"/farm/milk/production/{row['id']}",
        json={"morning_yield": 11},
    )
    assert rejected.status_code == 422, rejected.text
    assert container.repository_factory.session.query(
        MilkProductionCorrection
    ).count() == 0

    corrected = client.patch(
        f"/farm/milk/production/{row['id']}",
        json={
            "morning_yield": 11,
            "correction_reason": "Transcription error in morning sheet",
            "operator": "Auditor",
            "request_id": "milk-correction-audit-001",
        },
    )
    assert corrected.status_code == 200, corrected.text
    correction_id = corrected.json()["correction_id"]

    history = client.get(
        f"/farm/milk/production/{row['id']}/corrections"
    )
    assert history.status_code == 200, history.text
    correction = history.json()["corrections"][0]
    assert correction["id"] == correction_id
    assert correction["reason"] == "Transcription error in morning sheet"
    assert correction["operator"] == "Auditor"
    assert correction["before"]["total_yield"] == 25.0
    assert correction["after"]["total_yield"] == 26.0


def test_future_milk_production_is_rejected(client, registered_animal):
    future = _farm_day() + timedelta(days=1)
    response = _record_session(
        client,
        registered_animal,
        future,
        "MORNING",
        10,
    )

    assert response.status_code == 422, response.text
    assert container.repository_factory.milk().get_all() == []


def test_feed_events_are_timestamped_counted_and_do_not_consume_inventory(
    client,
    registered_animal,
):
    day = _farm_day()
    before = container.repository_factory.session.query(
        InventoryTransaction
    ).count()

    for index in range(5):
        response = client.post(
            "/farm/feed/records",
            json={
                "animal_id": registered_animal,
                "feed_type": "SILAGE",
                "quantity_kg": 1,
                "feeding_date": datetime.combine(
                    day,
                    time(hour=6 + index),
                ).isoformat(),
            },
        )
        assert response.status_code == 200, response.text

    status = client.get("/farm/feed/daily-status")
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["feeding_event_count"] == 5
    assert body["minimum_required_events"] == 5
    assert body["remaining_events"] == 0
    assert body["complete"] is True
    assert body["last_event_at"] is not None
    assert container.repository_factory.session.query(
        InventoryTransaction
    ).count() == before


def test_feed_date_only_is_not_accepted_as_a_timestamp(client):
    response = client.post(
        "/farm/feed/records",
        json={
            "group_or_pen": "MILKING",
            "feed_type": "SILAGE",
            "quantity_kg": 1,
            "feeding_date": _farm_day().isoformat(),
        },
    )

    assert response.status_code == 422, response.text


def test_non_milking_categories_are_not_auto_populated_from_herd_counts(client):
    created = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "lifecycle_status": "DRY",
            "is_currently_milking": False,
            "ear_tag": "AUDIT-DRY-001",
        },
    )
    assert created.status_code == 200, created.text

    summary = client.get("/farm/tmr")
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["herd_counts"]["Dry"] == 0
    dry = next(row for row in body["categories"] if row["category"] == "Dry")
    assert dry["population_authority"] == "MANUAL_GROUP_SIZE_REQUIRED"
    assert dry["category_cost_per_day"] == 0


def test_daily_tmr_snapshot_is_unique_and_sequentially_idempotent(client):
    existing_dates = {
        row.effective_date
        for row in container.repository_factory.feed_rations().get_active_for_group(
            DAILY_COST_SNAPSHOT_GROUP
        )
    }
    day = _farm_day() - timedelta(days=10)
    while day.isoformat() in existing_dates:
        day -= timedelta(days=1)
    first = lock_daily_tmr_cost_snapshot(
        container.repository_factory,
        operational_date=day,
    )
    second = lock_daily_tmr_cost_snapshot(
        container.repository_factory,
        operational_date=day,
    )

    assert first["created"] is True
    assert second["created"] is False
    rows = [
        row
        for row in container.repository_factory.feed_rations().get_active_for_group(
            DAILY_COST_SNAPSHOT_GROUP
        )
        if row.effective_date == day.isoformat()
    ]
    assert len(rows) == 1


def test_zero_temperature_survives_health_materialization(client, registered_animal):
    response = client.post(
        "/farm/health-observations",
        json={
            "animal_id": registered_animal,
            "symptom": "Audit zero temperature",
            "temperature_c": 0.0,
        },
    )
    assert response.status_code == 200, response.text

    observation = container.repository_factory.health().get_all()[0]
    assert observation.temperature == 0.0
    assert observation.temperature_c == 0.0
    assert observation.effective_temperature == 0.0


def test_health_case_resolution_rejects_whitespace_only_text(client, registered_animal):
    case = client.post(
        "/farm/health-cases",
        json={
            "animal_id": registered_animal,
            "severity": "MODERATE",
            "diagnosis": "Audit",
        },
    ).json()

    response = client.post(
        f"/farm/health-cases/{case['case_id']}/resolve",
        json={"resolution": "   "},
    )
    assert response.status_code == 422, response.text

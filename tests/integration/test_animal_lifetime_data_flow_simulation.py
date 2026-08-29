"""Input-driven lifetime Animal Passport simulation.

This test intentionally uses public operator entry points rather than direct
model insertion. The Passport is the final reconciliation surface for the
same permanent Animal ID.
"""


def _passport(client, animal_id):
    response = client.get(f"/farm/animals/{animal_id}/passport")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("animal", {}).get("animal_id") == animal_id, body
    assert "history" in body, body
    return body


def test_one_animal_public_entries_reconcile_into_complete_passport(
    client,
    registered_animal,
):
    health = client.post(
        "/farm/health-observations",
        json={
            "animal_id": registered_animal,
            "observation": "Normal appetite and movement",
            "temperature_c": 38.5,
            "severity": "NORMAL",
            "operator": "simulation",
        },
    )
    assert health.status_code == 200, health.text

    treatment = client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "SIMULATION-MEDICINE",
            "diagnosis": "Simulation treatment record",
            "dose": "10 ml",
            "treated_by": "simulation",
            "milk_withdrawal_days": 3,
            "notes": "Input-driven lifetime simulation",
            "operator": "simulation",
        },
    )
    assert treatment.status_code == 200, treatment.text

    breeding = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "HEAT_DETECTED",
            "technician": "simulation",
            "result": "OBSERVED",
            "notes": "Input-driven lifetime simulation",
            "operator": "simulation",
        },
    )
    assert breeding.status_code == 200, breeding.text

    feed = client.post(
        "/farm/feed",
        json={
            "animal_id": registered_animal,
            "feed_type": "SIMULATION-RATION",
            "quantity_kg": 12.5,
            "group_or_pen": "MILKING",
            "operator": "simulation",
        },
    )
    assert feed.status_code == 200, feed.text

    welfare = client.post(
        "/farm/welfare/observations",
        json={
            "animal_id": registered_animal,
            "welfare_domain": "BODY_CONDITION",
            "score": 82.0,
            "status": "OBSERVED",
            "notes": "Input-driven lifetime simulation",
            "recorded_by": "simulation",
        },
    )
    assert welfare.status_code == 200, welfare.text

    passport = _passport(client, registered_animal)
    history = passport["history"]

    assert any(
        row.get("animal_id") == registered_animal
        and row.get("observation") == "Normal appetite and movement"
        for row in history["health"]
    )
    assert any(
        row.get("animal_id") == registered_animal
        and row.get("medicine") == "SIMULATION-MEDICINE"
        for row in history["treatments"]
    )
    assert any(
        row.get("animal_id") == registered_animal
        and row.get("event_type") == "HEAT_DETECTED"
        for row in history["breeding"]
    )
    assert any(
        row.get("animal_id") == registered_animal
        and float(row.get("quantity_kg", 0)) == 12.5
        for row in history["feed"]
    )
    assert passport["record_counts"]["health"] >= 1
    assert passport["record_counts"]["treatments"] >= 1
    assert passport["record_counts"]["breeding"] >= 1
    assert passport["record_counts"]["feed"] >= 1
    assert passport["health_state"]["summary"]["treatment_count"] >= 1
    assert passport["biological_summary"]["active_milk_withdrawal"] is True

    welfare_rows = [
        row
        for row in history.get("welfare", [])
        if row.get("animal_id") == registered_animal
    ]
    assert welfare_rows == []
    assert passport["record_counts"].get("welfare", 0) == 0

def test_milk_traceability_is_linked_to_permanent_animal(client, registered_animal):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "afternoon_yield": 7.0,
            "operator": "Milking Operator",
        },
    )
    assert response.status_code == 200, response.text

    trace = client.get(f"/farm/milk/{registered_animal}/traceability")
    assert trace.status_code == 200, trace.text
    body = trace.json()
    assert body["data_status"] == "LIVE_PERSISTED"
    assert body["animal"]["animal_id"] == registered_animal
    assert body["record_count"] >= 1
    assert body["total_litres"] >= 15.0
    assert body["traceability_complete"] is True


def test_milk_traceability_rejects_unknown_animal(client):
    response = client.get("/farm/milk/AN-NOT-REGISTERED/traceability")
    assert response.status_code == 404

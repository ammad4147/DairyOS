from __future__ import annotations


def test_animal_timeline_uses_passport_history_and_is_chronological(
    client, registered_animal
):
    response = client.get(f"/farm/animals/{registered_animal}/timeline")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["animal_id"] == registered_animal
    assert isinstance(body["events"], list)
    assert isinstance(body["record_counts"], dict)
    timestamps = [event["timestamp"] for event in body["events"]]
    assert timestamps == sorted(timestamps)


def test_animal_timeline_rejects_unknown_animal(client):
    response = client.get("/farm/animals/DOES-NOT-EXIST/timeline")

    assert response.status_code == 404

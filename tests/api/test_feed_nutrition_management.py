def test_feed_ration_is_persisted_and_retrievable(client):
    response = client.post(
        "/farm/feed/rations",
        json={
            "name": "Lactating 25L",
            "animal_group": "LACTATING",
            "ingredients": [
                {"feed_type": "SILAGE", "quantity_kg": 18.0},
                {"feed_type": "SOYBEAN_MEAL", "quantity_kg": 2.0},
            ],
            "target_dmi_kg": 22.0,
            "dry_matter_pct": 42.0,
            "crude_protein_pct": 16.5,
            "ndf_pct": 30.0,
            "energy_mcal_kg": 1.55,
            "cost_per_kg": 0.42,
            "effective_date": "2026-08-12",
            "operator": "Feed Manager",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["ingredients"][0]["feed_type"] == "SILAGE"

    listed = client.get("/farm/feed/rations?animal_group=LACTATING")
    assert listed.status_code == 200, listed.text
    assert any(item["name"] == "Lactating 25L" for item in listed.json())


def test_feed_record_is_persisted_and_overview_uses_real_records(client, registered_animal):
    response = client.post(
        "/farm/feed/records",
        json={
            "animal_id": registered_animal,
            "feed_type": "SILAGE",
            "quantity_kg": 18.5,
            "notes": "Morning ration delivery",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["data_status"] == "LIVE_PERSISTED_DATA"

    records = client.get("/farm/feed/records")
    assert records.status_code == 200, records.text
    assert any(item["animal_id"] == registered_animal and item["quantity_kg"] == 18.5 for item in records.json())

    overview = client.get("/farm/feed/overview")
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["feeding_records"] >= 1
    assert body["total_recorded_feed_kg"] >= 18.5
    assert body["nutrition_metrics"]["dry_matter_intake_kg"] is None


def test_feed_record_requires_positive_quantity_and_known_animal(client, registered_animal):
    negative = client.post(
        "/farm/feed/records",
        json={
            "animal_id": registered_animal,
            "feed_type": "SILAGE",
            "quantity_kg": 0,
        },
    )
    assert negative.status_code == 422

    unknown = client.post(
        "/farm/feed/records",
        json={
            "animal_id": "AN-NOT-REGISTERED",
            "feed_type": "SILAGE",
            "quantity_kg": 10,
        },
    )
    assert unknown.status_code == 422

def test_youngstock_overview_reads_registered_youngstock(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "CALF", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    overview = client.get("/farm/youngstock/overview")
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["youngstock_count"] >= 1
    assert any(row["animal_id"] == registered_animal for row in body["animals"])


def test_youngstock_growth_and_weaning_are_recorded(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "CALF", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    growth = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={
            "weight_kg": 78.5,
            "height_cm": 91.0,
            "body_condition_score": 3.0,
            "operator": "Farm Operator",
        },
    )
    assert growth.status_code == 200, growth.text

    weaning = client.post(
        f"/farm/youngstock/{registered_animal}/weaning",
        json={
            "weight_kg": 82.0,
            "starter_feed_kg_day": 1.8,
            "method": "STANDARD",
            "operator": "Farm Operator",
        },
    )
    assert weaning.status_code == 200, weaning.text

    profile = client.get(f"/farm/youngstock/{registered_animal}")
    assert profile.status_code == 200, profile.text
    body = profile.json()
    assert body["animal_id"] == registered_animal
    assert body["latest_growth"]["weight_kg"] == 78.5
    assert body["latest_weaning"]["weight_kg"] == 82.0


def test_youngstock_rejects_non_positive_growth_weight(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "CALF", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    response = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 0, "operator": "Farm Operator"},
    )
    assert response.status_code == 422


def test_youngstock_rejects_growth_for_milking_animal(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "LACTATING", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    response = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 100, "operator": "Farm Operator"},
    )
    assert response.status_code == 409

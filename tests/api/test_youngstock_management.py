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
    assert body["body_development"]["latest_weight_kg"] == 78.5
    assert body["body_development"]["measurement_count"] == 1
    assert body["weaning_summary"]["weaned"] is True
    assert {item["status"] for item in body["management_checklist"]} == {"NOT_RECORDED", "COMPLETE", "HISTORICAL_CONTEXT_REQUIRED"}
    assert body["management_warnings"] == []


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


def test_body_development_continues_after_calf_stage(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "LACTATING", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    response = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 100, "operator": "Farm Operator"},
    )
    assert response.status_code == 200, response.text


def test_youngstock_rejects_invalid_bcs_and_future_measurement(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "CALF", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    invalid_bcs = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 50, "body_condition_score": 3.1},
    )
    assert invalid_bcs.status_code == 422

    future = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 50, "measured_at": "2999-01-01"},
    )
    assert future.status_code == 422


def test_youngstock_rejects_duplicate_measurement_and_weaning(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "CALF", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    first = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 50, "measured_at": "2026-01-10"},
    )
    assert first.status_code == 200, first.text
    duplicate = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 51, "measured_at": "2026-01-10"},
    )
    assert duplicate.status_code == 409

    weaning = client.post(
        f"/farm/youngstock/{registered_animal}/weaning",
        json={"weaned_at": "2026-01-11", "operator": "Farm Operator"},
    )
    assert weaning.status_code == 200, weaning.text
    duplicate_weaning = client.post(
        f"/farm/youngstock/{registered_animal}/weaning",
        json={"weaned_at": "2026-01-12", "operator": "Farm Operator"},
    )
    assert duplicate_weaning.status_code == 409


def test_youngstock_care_is_evidence_based_and_deduplicated(client, registered_animal):
    lifecycle = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={"lifecycle_status": "CALF", "operator": "Farm Operator"},
    )
    assert lifecycle.status_code == 200, lifecycle.text

    care = client.post(
        f"/farm/youngstock/{registered_animal}/care",
        json={"care_type": "FIRST_COLOSTRUM", "completed_at": "2026-01-10", "quantity_liters": 3.0},
    )
    assert care.status_code == 200, care.text
    duplicate = client.post(
        f"/farm/youngstock/{registered_animal}/care",
        json={"care_type": "FIRST_COLOSTRUM", "completed_at": "2026-01-11"},
    )
    assert duplicate.status_code == 409

    profile = client.get(f"/farm/youngstock/{registered_animal}")
    assert profile.status_code == 200, profile.text
    checklist = {row["key"]: row for row in profile.json()["management_checklist"]}
    assert checklist["newborn_care"]["status"] == "HISTORICAL_CONTEXT_REQUIRED"
    assert profile.json()["care_records"][0]["care_type"] == "FIRST_COLOSTRUM"


def test_youngstock_overdue_care_resolves_from_authoritative_evidence(client, registered_animal):
    profile_update = client.patch(
        f"/farm/animals/{registered_animal}",
        json={
            "lifecycle_status": "CALF",
            "date_of_birth": "2026-09-19",
            "operator": "Farm Operator",
        },
    )
    assert profile_update.status_code == 200, profile_update.text

    before = client.get(f"/farm/youngstock/{registered_animal}")
    assert before.status_code == 200, before.text
    overdue = {row["key"]: row for row in before.json()["management_checklist"]}
    assert overdue["first_colostrum"]["status"] == "OVERDUE"
    assert overdue["navel_care"]["status"] == "OVERDUE"
    assert {row["title"] for row in before.json()["management_warnings"]} == {
        "First colostrum recorded",
        "Navel care recorded",
    }

    care = client.post(
        f"/farm/youngstock/{registered_animal}/care",
        json={"care_type": "FIRST_COLOSTRUM", "completed_at": "2026-09-19"},
    )
    assert care.status_code == 200, care.text

    after = client.get(f"/farm/youngstock/{registered_animal}")
    assert after.status_code == 200, after.text
    checklist = {row["key"]: row for row in after.json()["management_checklist"]}
    assert checklist["first_colostrum"]["status"] == "COMPLETE"
    assert checklist["navel_care"]["status"] == "OVERDUE"
    assert [row["title"] for row in after.json()["management_warnings"]] == [
        "Navel care recorded"
    ]


def test_historical_calf_does_not_receive_retrospective_newborn_warnings(client, registered_animal):
    updated = client.patch(
        f"/farm/animals/{registered_animal}",
        json={
            "lifecycle_status": "CALF",
            "date_of_birth": "2025-01-01",
            "operator": "Farm Operator",
        },
    )
    assert updated.status_code == 200, updated.text

    profile = client.get(f"/farm/youngstock/{registered_animal}")
    assert profile.status_code == 200, profile.text
    body = profile.json()
    checklist = {row["key"]: row for row in body["management_checklist"]}
    assert checklist["newborn_care"]["status"] == "HISTORICAL_CONTEXT_REQUIRED"
    assert body["management_warnings"] == []


def test_male_calf_uses_shared_growth_and_care_cycle_without_female_rules(client, registered_animal):
    updated = client.patch(
        f"/farm/animals/{registered_animal}",
        json={
            "lifecycle_status": "CALF",
            "sex": "MALE",
            "date_of_birth": "2026-09-19",
            "operator": "Farm Operator",
        },
    )
    assert updated.status_code == 200, updated.text

    growth = client.post(
        f"/farm/youngstock/{registered_animal}/growth",
        json={"weight_kg": 42.0, "body_condition_score": 3.0},
    )
    assert growth.status_code == 200, growth.text
    care = client.post(
        f"/farm/youngstock/{registered_animal}/care",
        json={"care_type": "NAVEL_CARE", "completed_at": "2026-09-19"},
    )
    assert care.status_code == 200, care.text

    profile = client.get(f"/farm/youngstock/{registered_animal}")
    assert profile.status_code == 200, profile.text
    body = profile.json()
    assert body["sex"] == "MALE"
    assert body["body_development"]["latest_weight_kg"] == 42.0
    assert any(row["key"] == "navel_care" and row["status"] == "COMPLETE" for row in body["management_checklist"])

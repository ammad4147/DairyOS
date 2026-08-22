"""Regression coverage for the authoritative Herd/Animal CRUD surface."""


def test_list_animals_uses_persistent_register(client, registered_animal):
    response = client.get("/farm/animals")
    assert response.status_code == 200
    records = response.json()
    assert any(record["animal_id"] == registered_animal for record in records)


def test_update_animal_profile(client, registered_animal):
    response = client.patch(
        f"/farm/animals/{registered_animal}",
        json={
            "breed": "Holstein Friesian",
            "rfid": "RFID-TEST-001",
            "production_group": "HIGH_YIELD",
            "location": "Shed A",
            "operator": "Tester",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["animal_id"] == registered_animal
    assert data["rfid"] == "RFID-TEST-001"
    assert data["production_group"] == "HIGH_YIELD"
    assert data["location"] == "Shed A"


def test_lifecycle_change_preserves_governed_validation(client, registered_animal):
    response = client.patch(
        f"/farm/animals/{registered_animal}/lifecycle",
        json={
            "lifecycle_status": "LACTATING",
            "status": "ACTIVE",
            "operator": "Tester",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["lifecycle_status"] == "LACTATING"
    assert response.json()["is_currently_milking"] is True


def test_invalid_lifecycle_is_rejected(client, registered_animal):
    response = client.patch(
        f"/farm/animals/{registered_animal}",
        json={"lifecycle_status": "NOT_A_REAL_STATUS"},
    )
    assert response.status_code == 422


def test_retire_animal_is_soft_deactivation(client, registered_animal):
    response = client.delete(f"/farm/animals/{registered_animal}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["animal_id"] == registered_animal
    assert data["active"] is False
    assert data["status"] == "INACTIVE"

    get_response = client.get(f"/farm/animals/{registered_animal}")
    assert get_response.status_code == 200
    assert get_response.json()["active"] is False


def test_retired_animal_can_be_reactivated(client, registered_animal):
    retire = client.delete(f"/farm/animals/{registered_animal}")
    assert retire.status_code == 200

    activate = client.post(
        f"/farm/animals/{registered_animal}/activate",
        json={"operator": "Tester"},
    )
    assert activate.status_code == 200, activate.text
    data = activate.json()
    assert data["active"] is True
    assert data["status"] == "ACTIVE"


def test_milking_frequency_change_remains_animal_passport_rule(client, registered_animal):
    response = client.post(
        f"/farm/animals/{registered_animal}/milking-frequency",
        json={
            "milking_frequency": "THRICE_DAILY",
            "changed_by": "Tester",
            "reason": "Herd CRUD regression",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["milking_frequency"] == "THRICE_DAILY"

    history = client.get(
        f"/farm/animals/{registered_animal}/milking-frequency/history"
    )
    assert history.status_code == 200
    assert any(
        item["milking_frequency"] == "THRICE_DAILY"
        for item in history.json()
    )

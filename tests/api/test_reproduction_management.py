from dairyos.data.repositories.repository_factory import RepositoryFactory


def test_reproduction_overview_reads_persisted_breeding_records(client, registered_animal):
    response = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "insemination",
            "technician": "Dr Vet",
            "result": "completed",
            "operator": "Dr Vet",
        },
    )
    assert response.status_code == 200, response.text

    pregnancy = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "pregnancy_check",
            "technician": "Dr Vet",
            "result": "pregnant",
            "operator": "Dr Vet",
        },
    )
    assert pregnancy.status_code == 200, pregnancy.text

    overview = client.get("/farm/reproduction/overview")
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["inseminations"] >= 1
    assert body["pregnancy_checks"] >= 1
    assert body["confirmed_pregnancies"] >= 1
    assert body["conception_rate_percent"] == 100.0
    assert any(row["animal_id"] == registered_animal for row in body["records"])


def test_reproduction_overview_supports_operator_ui_event_vocabulary(client, registered_animal):
    for event_type, result in (
        ("insemination", "completed"),
        ("pregnancy_diagnosis", "pregnant"),
        ("pregnancy_confirmed", "confirmed"),
        ("calving", "completed"),
    ):
        response = client.post(
            "/farm/breeding",
            json={
                "animal_id": registered_animal,
                "event_type": event_type,
                "technician": "Dr Vet",
                "result": result,
                "operator": "Dr Vet",
            },
        )
        assert response.status_code == 200, response.text

    body = client.get("/farm/reproduction/overview").json()
    assert body["inseminations"] == 1
    assert body["pregnancy_checks"] == 1
    # pregnancy_diagnosis + pregnancy_confirmed are two positive observations
    # of the same conception. They must not be double-counted as conceptions.
    assert body["confirmed_pregnancies"] == 1
    assert body["calvings"] == 1
    assert body["conception_rate_percent"] == 100.0


def test_animal_reproduction_history_uses_permanent_animal_id(client, registered_animal):
    response = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "insemination",
            "technician": "Dr Vet",
            "result": "completed",
            "operator": "Dr Vet",
        },
    )
    assert response.status_code == 200, response.text

    history = client.get(f"/farm/reproduction/animals/{registered_animal}")
    assert history.status_code == 200, history.text
    body = history.json()
    assert body["animal_id"] == registered_animal
    assert body["record_count"] >= 1
    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["latest_event"]["event_type"] == "insemination"


def test_animal_reproduction_history_rejects_unknown_animal(client):
    response = client.get("/farm/reproduction/animals/AN-DOES-NOT-EXIST")
    assert response.status_code == 404


def test_reproduction_overview_has_no_synthetic_data(client):
    response = client.get("/farm/reproduction/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["data_status"] in {"NO_DATA", "LIVE_PERSISTED_DATA"}
    assert body["record_count"] == len(body["records"])

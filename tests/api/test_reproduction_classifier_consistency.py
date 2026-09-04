"""Cross-endpoint breeding classifier and biological-sequence consistency."""


def _record_breeding(client, animal_id, event_type, result):
    response = client.post(
        "/farm/breeding",
        json={
            "animal_id": animal_id,
            "event_type": event_type,
            "technician": "Dr Vet",
            "result": result,
            "operator": "Dr Vet",
        },
    )
    assert response.status_code == 200, response.text
    return response


def test_pregnancy_diagnosis_is_confirmed_on_every_live_endpoint(
    client, registered_animal
):
    _record_breeding(client, registered_animal, "insemination", "completed")
    _record_breeding(client, registered_animal, "pregnancy_diagnosis", "pregnant")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["confirmed_pregnancies"] == 1
    assert reproduction["pregnancy_checks"] == 1
    assert reproduction["conception_rate_percent"] == 100.0

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["confirmed_pregnancies"] == 1
    assert kpis["kpis"]["pregnancy_checks"] == 1
    assert kpis["kpis"]["conception_rate_percent"] == 100.0

    status = client.get(
        f"/farm/animals/{registered_animal}/reproduction"
    ).json()
    assert status["state"] == "PREGNANT"


def test_pregnancy_confirmation_without_insemination_is_rejected(
    client, registered_animal
):
    response = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "pregnancy_confirmed",
            "technician": "Dr Vet",
            "result": "confirmed",
            "operator": "Dr Vet",
        },
    )
    assert response.status_code == 409

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["confirmed_pregnancies"] == 0
    assert reproduction["pregnancy_checks"] == 0


def test_negative_pd_requires_insemination_and_then_returns_open(
    client, registered_animal
):
    rejected = client.post(
        "/farm/breeding",
        json={
            "animal_id": registered_animal,
            "event_type": "pregnancy_negative",
            "technician": "Dr Vet",
            "result": "open",
            "operator": "Dr Vet",
        },
    )
    assert rejected.status_code == 409

    _record_breeding(client, registered_animal, "insemination", "completed")
    _record_breeding(client, registered_animal, "pregnancy_diagnosis", "open")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["pregnancy_checks"] == 1
    assert reproduction["confirmed_pregnancies"] == 0

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["pregnancy_checks"] == 1
    assert kpis["kpis"]["confirmed_pregnancies"] is None

    status = client.get(
        f"/farm/animals/{registered_animal}/reproduction"
    ).json()
    assert status["state"] == "OPEN"


def test_full_event_sequence_agrees_across_all_three_endpoints(
    client, registered_animal
):
    _record_breeding(client, registered_animal, "insemination", "completed")
    _record_breeding(client, registered_animal, "pregnancy_diagnosis", "pregnant")
    _record_breeding(client, registered_animal, "calving", "completed")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["inseminations"] == 1
    assert reproduction["pregnancy_checks"] == 1
    assert reproduction["confirmed_pregnancies"] == 1
    assert reproduction["calvings"] == 1

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["inseminations"] == 1
    assert kpis["kpis"]["pregnancy_checks"] == 1
    assert kpis["kpis"]["confirmed_pregnancies"] == 1
    assert (
        kpis["kpis"]["conception_rate_percent"]
        == reproduction["conception_rate_percent"]
    )

    status = client.get(
        f"/farm/animals/{registered_animal}/reproduction"
    ).json()
    assert status["state"] in {"CALVED", "LACTATING"}
    assert status["pregnancy_status"] != "PREGNANT"

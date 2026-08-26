"""Guards G6.1 (breeding classifier unification, Phase 1, 2026-08-14).

These tests submit events using the real operator vocabulary and assert
/farm/animals/{id}/reproduction, /farm/reproduction/overview and
/farm/kpis/overview agree, using the shared
reproductive_event_classifier and reproduction KPI authority.

A positive pregnancy diagnosis and a later pregnancy_confirmed event are two
observations of the same conception; they must therefore produce one confirmed
pregnancy/conception rather than inflating the KPI by counting observations.
"""


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


def test_pregnancy_diagnosis_is_confirmed_on_every_live_endpoint(client, registered_animal):
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

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] == "PREGNANT"


def test_bare_pregnancy_confirmed_event_is_confirmed_everywhere(client, registered_animal):
    _record_breeding(client, registered_animal, "pregnancy_confirmed", "confirmed")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["confirmed_pregnancies"] == 1
    assert reproduction["pregnancy_checks"] == 0

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["confirmed_pregnancies"] == 1
    assert kpis["kpis"]["pregnancy_checks"] is None

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] == "PREGNANT"


def test_pregnancy_negative_is_a_check_but_not_confirmed(client, registered_animal):
    _record_breeding(client, registered_animal, "pregnancy_negative", "open")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["pregnancy_checks"] == 1
    assert reproduction["confirmed_pregnancies"] == 0

    kpis = client.get("/farm/kpis/overview?days=365").json()
    assert kpis["kpis"]["pregnancy_checks"] == 1
    assert kpis["kpis"]["confirmed_pregnancies"] is None

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] == "OPEN"


def test_full_event_sequence_agrees_across_all_three_endpoints(client, registered_animal):
    _record_breeding(client, registered_animal, "heat_detected", "detected")
    _record_breeding(client, registered_animal, "insemination", "completed")
    _record_breeding(client, registered_animal, "pregnancy_diagnosis", "pregnant")
    _record_breeding(client, registered_animal, "pregnancy_confirmed", "confirmed")
    _record_breeding(client, registered_animal, "calving", "completed")

    reproduction = client.get("/farm/reproduction/overview").json()
    assert reproduction["heat_detections"] == 1
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

    status = client.get(f"/farm/animals/{registered_animal}/reproduction").json()
    assert status["state"] in {"CALVED", "LACTATING"}
    assert status["pregnancy_status"] != "PREGNANT"

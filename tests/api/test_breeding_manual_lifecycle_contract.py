"""Runtime contracts for form-governed breeding lifecycle transitions."""

import pytest


def _record(client, animal_id: str, event_type: str, result: str):
    return client.post(
        "/farm/breeding",
        json={
            "animal_id": animal_id,
            "event_type": event_type,
            "technician": "Dr Vet",
            "result": result,
            "operator": "Dr Vet",
        },
    )


def _establish_confirmed_pregnancy(client, animal_id: str):
    insemination = _record(client, animal_id, "insemination", "COMPLETED")
    assert insemination.status_code == 200, insemination.text

    diagnosis = _record(client, animal_id, "pregnancy_confirmed", "POSITIVE")
    assert diagnosis.status_code == 200, diagnosis.text

    state = client.get(f"/farm/animals/{animal_id}/reproduction")
    assert state.status_code == 200, state.text
    assert state.json()["state"] == "PREGNANT"


def test_pd_calving_and_pregnancy_loss_require_prior_manual_state(
    client, registered_animal
):
    pd = _record(client, registered_animal, "pregnancy_confirmed", "POSITIVE")
    calving = _record(client, registered_animal, "calving", "COMPLETED")
    miscarriage = _record(client, registered_animal, "pregnancy_lost", "MISCARRIAGE")
    abortion = _record(client, registered_animal, "abortion", "ABORTED")

    assert pd.status_code == 409
    assert calving.status_code == 409
    assert miscarriage.status_code == 409
    assert abortion.status_code == 409


@pytest.mark.parametrize(
    ("event_type", "submitted_result", "canonical_result"),
    [
        ("pregnancy_lost", "MISCARRIAGE", "MISCARRIAGE"),
        ("abortion", "ABORTED", "ABORTED"),
    ],
)
def test_manual_pregnancy_loss_is_accepted_only_after_confirmed_pregnancy_and_propagates(
    client,
    registered_animal,
    event_type,
    submitted_result,
    canonical_result,
):
    _establish_confirmed_pregnancy(client, registered_animal)

    loss = _record(client, registered_animal, event_type, submitted_result)
    assert loss.status_code == 200, loss.text
    payload = loss.json()
    assert payload["event_type"] == event_type
    assert payload["result"] == canonical_result
    assert payload["reproductive_state"]["state"] == "OPEN"
    assert payload["reproductive_state"]["pregnancy_status"] != "PREGNANT"
    assert payload["reproductive_state"]["expected_calving_date"] is None

    state = client.get(f"/farm/animals/{registered_animal}/reproduction")
    assert state.status_code == 200, state.text
    state_payload = state.json()
    assert state_payload["state"] == "OPEN"
    assert state_payload["pregnancy_status"] != "PREGNANT"
    assert state_payload["expected_calving_date"] is None

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    reproduction = dashboard.json()["reproduction"]
    assert reproduction["pregnant"] == 0
    assert reproduction["inseminated"] == 0

    ledger = client.get("/farm/breeding")
    assert ledger.status_code == 200, ledger.text
    assert any(
        str(row.get("animal_id")) == registered_animal
        and str(row.get("event_type")) == event_type
        and str(row.get("result")) == canonical_result
        for row in ledger.json()
    )

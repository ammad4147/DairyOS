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


def test_insemination_enters_register_and_updates_current_state_and_dashboard(
    client, registered_animal
):
    insemination = _record(client, registered_animal, "insemination", "COMPLETED")
    assert insemination.status_code == 200, insemination.text

    state = client.get(f"/farm/animals/{registered_animal}/reproduction")
    assert state.status_code == 200, state.text
    assert state.json()["state"] == "INSEMINATED"

    ledger = client.get("/farm/breeding")
    assert ledger.status_code == 200, ledger.text
    assert any(
        str(row.get("animal_id")) == registered_animal
        and str(row.get("event_type")) == "insemination"
        for row in ledger.json()
    )

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    reproduction = dashboard.json()["reproduction"]
    assert reproduction["inseminated"] >= 1
    assert reproduction["pregnant"] == 0


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


def test_negative_pd_closes_the_insemination_cycle_everywhere(
    client, registered_animal
):
    insemination = _record(client, registered_animal, "insemination", "COMPLETED")
    assert insemination.status_code == 200, insemination.text

    negative = _record(client, registered_animal, "pregnancy_negative", "NEGATIVE")
    assert negative.status_code == 200, negative.text
    assert negative.json()["reproductive_state"]["state"] == "OPEN"

    state = client.get(f"/farm/animals/{registered_animal}/reproduction")
    assert state.status_code == 200, state.text
    state_payload = state.json()
    assert state_payload["state"] == "OPEN"
    assert state_payload["pregnancy_status"] == "NOT_PREGNANT"
    assert state_payload["expected_calving_date"] is None

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    reproduction = dashboard.json()["reproduction"]
    assert reproduction["pregnant"] == 0
    assert reproduction["inseminated"] == 0

    passport = client.get(f"/farm/animals/{registered_animal}/passport")
    assert passport.status_code == 200, passport.text
    passport_payload = passport.json()
    current = passport_payload["reproduction"]["current"]
    assert current["current_api_status"] == "OPEN"
    assert current["pregnancy_status"] == "NOT_PREGNANT"
    assert current["expected_calving_date"] is None
    assert any(
        event["event_type"] == "PREGNANCY_NEGATIVE"
        for event in passport_payload["reproduction"]["lifetime_events"]
    )


@pytest.mark.parametrize(
    ("event_type", "submitted_result", "canonical_result", "passport_event", "count_key"),
    [
        (
            "pregnancy_lost",
            "MISCARRIAGE",
            "MISCARRIAGE",
            "PREGNANCY_LOST",
            "miscarriages",
        ),
        ("abortion", "ABORTED", "ABORTED", "ABORTION", "abortions"),
    ],
)
def test_manual_pregnancy_loss_is_accepted_only_after_confirmed_pregnancy_and_propagates(
    client,
    registered_animal,
    event_type,
    submitted_result,
    canonical_result,
    passport_event,
    count_key,
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

    passport = client.get(f"/farm/animals/{registered_animal}/passport")
    assert passport.status_code == 200, passport.text
    passport_payload = passport.json()
    current = passport_payload["reproduction"]["current"]
    assert current["current_api_status"] == "OPEN"
    assert current["pregnancy_status"] == "NOT_PREGNANT"
    assert current["expected_calving_date"] is None
    assert current[count_key] == 1
    assert current["pregnancy_losses"] == 1
    assert any(
        event["event_type"] == passport_event
        for event in passport_payload["reproduction"]["lifetime_events"]
    )


def test_calving_requires_confirmed_pregnancy_and_updates_lifecycle_projections(
    client, registered_animal
):
    _establish_confirmed_pregnancy(client, registered_animal)

    calving = _record(client, registered_animal, "calving", "COMPLETED")
    assert calving.status_code == 200, calving.text
    calving_payload = calving.json()
    assert calving_payload["reproductive_state"]["state"] == "LACTATING"
    assert calving_payload["reproductive_state"]["pregnancy_status"] == "NOT_PREGNANT"

    state = client.get(f"/farm/animals/{registered_animal}/reproduction")
    assert state.status_code == 200, state.text
    state_payload = state.json()
    assert state_payload["state"] == "LACTATING"
    assert state_payload["pregnancy_status"] == "NOT_PREGNANT"
    assert state_payload["last_calving_date"] is not None

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    reproduction = dashboard.json()["reproduction"]
    assert reproduction["pregnant"] == 0
    assert reproduction["inseminated"] == 0

    passport = client.get(f"/farm/animals/{registered_animal}/passport")
    assert passport.status_code == 200, passport.text
    passport_payload = passport.json()
    current = passport_payload["reproduction"]["current"]
    assert current["pregnancy_status"] == "NOT_PREGNANT"
    assert current["last_calving_date"] is not None
    assert any(
        event["event_type"] == "CALVING"
        for event in passport_payload["reproduction"]["lifetime_events"]
    )

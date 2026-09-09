"""HealthCase (G5.1, 2026-08-14).

Before this, `HealthObservation` had a `status` field but no
status-transition endpoint -- an observation could be recorded, but
nothing modeled "this animal is currently being treated for X, watch it
until Y, here's how it was resolved." Decision (build-spec Session 5):
build a real `HealthCase` entity with its own `HL-YYMMDD-NNN` id, wrapping
observations[] + diagnosis + treatments[] + withdrawal_until +
follow_up_due_at + resolution. Resolution is always an explicit operator
action.
"""

import re

from dairyos.api.reference_data import GOVERNED


def _open_case(client, animal_id, **overrides):
    payload = {"animal_id": animal_id, "severity": "MODERATE", "diagnosis": "Mastitis"}
    payload.update(overrides)
    return client.post("/farm/health-cases", json=payload)


CASE_ID_PATTERN = re.compile(r"^HL-\d{6}-\d{3}$")


# ---------------------------------------------------------------------------
# Opening a case
# ---------------------------------------------------------------------------


def test_opening_a_case_generates_a_governed_id(client, registered_animal):
    response = _open_case(client, registered_animal)
    assert response.status_code == 200, response.text
    body = response.json()

    assert CASE_ID_PATTERN.match(body["case_id"]), body["case_id"]
    assert body["status"] == "OPEN"
    assert body["animal_id"] == registered_animal
    assert body["severity"] == "MODERATE"
    assert body["diagnosis"] == "Mastitis"
    assert body["resolved_at"] is None


def test_sequential_case_ids_on_the_same_day_increment(client, registered_animal):
    first = _open_case(client, registered_animal).json()
    second = _open_case(client, registered_animal).json()

    assert first["case_id"] != second["case_id"]
    first_seq = int(first["case_id"].rsplit("-", 1)[1])
    second_seq = int(second["case_id"].rsplit("-", 1)[1])
    assert second_seq == first_seq + 1


def test_ungoverned_severity_is_rejected(client, registered_animal):
    response = _open_case(client, registered_animal, severity="MILD")
    assert response.status_code == 422, response.text


def test_every_governed_severity_is_accepted(client, registered_animal):
    for severity in GOVERNED["health_severities"]:
        response = _open_case(client, registered_animal, severity=severity)
        assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Listing and retrieval
# ---------------------------------------------------------------------------


def test_list_health_cases_filters_by_animal(client, registered_animal):
    _open_case(client, registered_animal)
    other_response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "THRICE_DAILY",
            "ear_tag": "TEST-OTHERANIMAL",
        },
    )
    other_animal = other_response.json()["animal_id"]
    _open_case(client, other_animal)

    response = client.get("/farm/health-cases", params={"animal_id": registered_animal})
    assert response.status_code == 200, response.text
    cases = response.json()["cases"]
    assert len(cases) == 1
    assert cases[0]["animal_id"] == registered_animal


def test_get_case_by_case_id_includes_wrapped_observations_and_treatments(
    client, registered_animal
):
    case = _open_case(client, registered_animal).json()

    obs = client.post(
        "/farm/health-observations",
        json={
            "animal_id": registered_animal,
            "observation": "High temperature",
            "severity": "SEVERE",
            "health_case_id": case["id"],
        },
    )
    assert obs.status_code == 200, obs.text

    treatment = client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "Amoxicillin",
            "milk_withdrawal_days": 3,
            "health_case_id": case["id"],
        },
    )
    assert treatment.status_code == 200, treatment.text

    response = client.get(f"/farm/health-cases/{case['case_id']}")
    assert response.status_code == 200, response.text
    body = response.json()

    assert len(body["observations"]) == 1
    assert body["observations"][0]["observation"] == "High temperature"
    assert len(body["treatments"]) == 1
    assert body["treatments"][0]["medicine"] == "Amoxicillin"


def test_get_unknown_case_id_is_404(client):
    response = client.get("/farm/health-cases/HL-999999-999")
    assert response.status_code == 404, response.text


# ---------------------------------------------------------------------------
# Linking validation
# ---------------------------------------------------------------------------


def test_linking_observation_to_nonexistent_case_is_rejected(client, registered_animal):
    response = client.post(
        "/farm/health-observations",
        json={
            "animal_id": registered_animal,
            "observation": "Lethargic",
            "health_case_id": 999999,
        },
    )
    assert response.status_code == 404, response.text


def test_linking_treatment_to_nonexistent_case_is_rejected(client, registered_animal):
    response = client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "Amoxicillin",
            "milk_withdrawal_days": 3,
            "health_case_id": 999999,
        },
    )
    assert response.status_code == 404, response.text


# ---------------------------------------------------------------------------
# Withdrawal aggregation -- the case always reflects the LATEST known
# withdrawal date across everything wrapped into it.
# ---------------------------------------------------------------------------


def test_linked_treatment_raises_the_cases_withdrawal_until(client, registered_animal):
    case = _open_case(client, registered_animal).json()
    assert case["withdrawal_until"] is None

    client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "Amoxicillin",
            "milk_withdrawal_days": 3,
            "health_case_id": case["id"],
        },
    )

    after_first = client.get(f"/farm/health-cases/{case['case_id']}").json()
    assert after_first["withdrawal_until"] is not None

    client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "Penicillin",
            "milk_withdrawal_days": 10,
            "health_case_id": case["id"],
        },
    )

    after_second = client.get(f"/farm/health-cases/{case['case_id']}").json()
    assert after_second["withdrawal_until"] > after_first["withdrawal_until"]


def test_a_shorter_second_treatment_never_lowers_the_cases_withdrawal_until(
    client, registered_animal
):
    case = _open_case(client, registered_animal).json()

    client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "Penicillin",
            "milk_withdrawal_days": 10,
            "health_case_id": case["id"],
        },
    )
    after_long = client.get(f"/farm/health-cases/{case['case_id']}").json()

    client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "Amoxicillin",
            "milk_withdrawal_days": 1,
            "health_case_id": case["id"],
        },
    )
    after_short = client.get(f"/farm/health-cases/{case['case_id']}").json()

    assert after_short["withdrawal_until"] == after_long["withdrawal_until"]


# ---------------------------------------------------------------------------
# Resolution -- explicit operator action only.
# ---------------------------------------------------------------------------


def test_resolving_a_case_sets_status_and_resolution(client, registered_animal):
    case = _open_case(client, registered_animal).json()

    response = client.post(
        f"/farm/health-cases/{case['case_id']}/resolve",
        json={"resolution": "Full recovery, withdrawal cleared", "resolved_by": "Dr. Vet"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "RESOLVED"
    assert body["resolution"] == "Full recovery, withdrawal cleared"
    assert body["resolved_by"] == "Dr. Vet"
    assert body["resolved_at"] is not None


def test_resolving_an_already_resolved_case_is_rejected(client, registered_animal):
    case = _open_case(client, registered_animal).json()
    client.post(
        f"/farm/health-cases/{case['case_id']}/resolve",
        json={"resolution": "Recovered"},
    )

    second = client.post(
        f"/farm/health-cases/{case['case_id']}/resolve",
        json={"resolution": "Recovered again?"},
    )
    assert second.status_code == 409, second.text


def test_resolving_an_unknown_case_is_404(client):
    response = client.post(
        "/farm/health-cases/HL-999999-999/resolve",
        json={"resolution": "N/A"},
    )
    assert response.status_code == 404, response.text


def test_a_case_remains_open_after_an_observation_is_linked(client, registered_animal):
    """Resolution must never be inferred -- only the explicit /resolve action."""

    case = _open_case(client, registered_animal).json()
    client.post(
        "/farm/health-observations",
        json={
            "animal_id": registered_animal,
            "observation": "Improving",
            "health_case_id": case["id"],
        },
    )

    refreshed = client.get(f"/farm/health-cases/{case['case_id']}").json()
    assert refreshed["status"] == "OPEN"

from datetime import datetime

from dairyos.core.time_utils import utcnow


def test_utc_event_does_not_make_calving_assertion_depend_on_local_midnight(client, registered_animal):
    """A regression assertion must not depend on the CI runner's wall clock.

    DairyOS operational date is farm-local (Asia/Karachi), while persisted
    breeding timestamps are UTC. The endpoint may expose either CALVED or
    LACTATING immediately after a recorded calving depending on the
    operational-date boundary. The stable invariant is that calving exists
    and the animal is no longer pregnant.
    """
    for event_type, result in (
        ("heat_detected", "detected"),
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

    status = client.get(
        f"/farm/animals/{registered_animal}/reproduction"
    ).json()

    assert status["last_calving"]
    datetime.fromisoformat(status["last_calving"])
    assert status["state"] in {"CALVED", "LACTATING"}
    assert status["pregnancy_status"] != "PREGNANT"
    assert utcnow() is not None

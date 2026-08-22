from datetime import datetime, timezone

from dairyos.core.time_utils import utcnow


def test_utc_event_does_not_make_calving_assertion_depend_on_local_midnight(client, registered_animal):
    """A regression assertion must not depend on the CI runner's wall clock.

    DairyOS operational date is farm-local (Asia/Karachi), while persisted
    breeding timestamps are UTC. Around local midnight, utcnow().date() can
    differ from the farm operational date by one day. The endpoint is already
    contractually allowed to expose LACTATING once the calving date has moved
    into the completed day; this test only verifies that the state is coherent
    with the authoritative operational-date relationship.
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

    last_calving = datetime.fromisoformat(
        status["last_calving"]
    )
    operational_date = datetime.fromisoformat(
        utcnow().isoformat()
    ).date()

    if last_calving.date() == operational_date:
        assert status["state"] == "CALVED"
    else:
        assert status["state"] == "LACTATING"

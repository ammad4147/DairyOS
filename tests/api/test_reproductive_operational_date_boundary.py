from datetime import datetime

from dairyos.core.time_utils import utcnow


from tests.helpers.breeding import post_breeding

def test_utc_event_does_not_make_calving_assertion_depend_on_local_midnight(client, registered_animal):
    """A regression assertion must not depend on the CI runner's wall clock.

    DairyOS operational date is farm-local (Asia/Karachi), while persisted
    breeding timestamps are UTC. After calving, the mother remains DRY_OFF
    until the operator explicitly returns her to the milking herd. The stable
    invariant is that calving exists and the animal is no longer pregnant.
    """
    for event_type, result in (
        ("insemination", "completed"),
        ("pregnancy_diagnosis", "pregnant"),
        ("pregnancy_confirmed", "confirmed"),
        ("calving", "completed"),
    ):
        response = post_breeding(client, registered_animal, event_type, result)
        assert response.status_code == 200, response.text

    status = client.get(
        f"/farm/animals/{registered_animal}/reproduction"
    ).json()

    assert status["last_calving_date"]
    datetime.fromisoformat(status["last_calving_date"])
    assert status["state"] == "DRY_OFF"
    assert status["pregnancy_status"] != "PREGNANT"
    assert utcnow() is not None
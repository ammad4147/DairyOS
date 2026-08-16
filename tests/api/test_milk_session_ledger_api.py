"""End-to-end tests for the milking session ledger and sequencing (G3.1/G1.6).

The behaviour under test is what an operator experiences: what the API accepts,
what it refuses, and whether the refusal tells them how to proceed.
"""

from datetime import date, timedelta

from dairyos.app import container


TODAY = date(2026, 8, 13)
YESTERDAY = TODAY - timedelta(days=1)


def _milk_rows(animal_id):
    factory = container.repository_factory
    factory.session.expire_all()
    return factory.milk().get_by_animal_id(animal_id)


def _ledger_rows():
    factory = container.repository_factory
    factory.session.expire_all()
    return factory.milking_session_ledger().get_all()


def _record_milk(client, animal_id, session, day=TODAY, **yields):
    return client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "milking_session": session,
            "production_date": day.isoformat(),
            "operator": "Milking Operator",
            **yields,
        },
    )


# ----------------------------------------------------------------------
# The ledger
# ----------------------------------------------------------------------

def test_recording_a_session_settles_it_in_the_ledger(
    client, registered_animal
):
    response = _record_milk(
        client, registered_animal, "MORNING", morning_yield=9.0
    )

    assert response.status_code == 200, response.text
    assert response.json()["session_record_id"] == "MS-260813-001"

    rows = _ledger_rows()
    assert len(rows) == 1
    assert rows[0].milking_session == "MORNING"
    assert rows[0].status == "RECORDED"


def test_a_second_animal_does_not_open_a_second_ledger_row(
    client, registered_animal
):
    _record_milk(client, registered_animal, "MORNING", morning_yield=9.0)
    _record_milk(client, registered_animal, "MORNING", morning_yield=4.0)

    assert len(_ledger_rows()) == 1


# ----------------------------------------------------------------------
# Sequencing
# ----------------------------------------------------------------------

def test_evening_is_refused_while_the_morning_is_unaccounted_for(
    client, registered_animal
):
    # Establish the ledger on an earlier day so sequencing is live.
    assert client.post(
        "/farm/milk/not-milked",
        json={
            "milking_session": "MORNING",
            "reason": "POWER_OUTAGE",
            "operational_date": YESTERDAY.isoformat(),
        },
    ).status_code == 200

    response = _record_milk(
        client, registered_animal, "EVENING", evening_yield=7.0
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["error"] == "MILKING_SESSION_OUT_OF_SEQUENCE"
    assert detail["next_session"] == "MORNING"
    assert {item["action"] for item in detail["resolutions"]} == {
        "RECORD_SESSION",
        "DECLARE_NOT_MILKED",
    }

    # Nothing was written on a refusal.
    assert _milk_rows(registered_animal) == []


def test_declaring_the_skip_unblocks_the_rest_of_the_day(
    client, registered_animal
):
    client.post(
        "/farm/milk/not-milked",
        json={
            "milking_session": "MORNING",
            "reason": "EQUIPMENT_FAILURE",
            "operational_date": TODAY.isoformat(),
        },
    )

    response = _record_milk(
        client, registered_animal, "EVENING", evening_yield=7.0
    )

    assert response.status_code == 200, response.text


def test_an_entry_with_no_session_is_not_sequenced(client, registered_animal):
    client.post(
        "/farm/milk/not-milked",
        json={
            "milking_session": "MORNING",
            "reason": "WEATHER",
            "operational_date": YESTERDAY.isoformat(),
        },
    )

    # A legacy caller that never named a session has nothing to be out of
    # sequence with, and must not be pushed back into guessing one.
    response = client.post(
        "/farm/milk",
        json={"animal_id": registered_animal, "morning_yield": 5.0},
    )

    assert response.status_code == 200, response.text
    assert len(_ledger_rows()) == 1
    assert _milk_rows(registered_animal)[0].session_ledger is False


# ----------------------------------------------------------------------
# Declaring a session not milked
# ----------------------------------------------------------------------

def test_not_milked_requires_a_governed_reason(client):
    response = client.post(
        "/farm/milk/not-milked",
        json={"milking_session": "MORNING", "reason": "the pump broke"},
    )

    assert response.status_code == 422


def test_reason_other_requires_notes(client):
    response = client.post(
        "/farm/milk/not-milked",
        json={
            "milking_session": "MORNING",
            "reason": "OTHER",
            "operational_date": TODAY.isoformat(),
        },
    )

    assert response.status_code == 422
    assert "notes" in response.json()["detail"]


def test_a_settled_session_cannot_be_restated(client):
    payload = {
        "milking_session": "MORNING",
        "reason": "POWER_OUTAGE",
        "operational_date": TODAY.isoformat(),
    }

    assert client.post("/farm/milk/not-milked", json=payload).status_code == 200

    response = client.post("/farm/milk/not-milked", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == (
        "MILKING_SESSION_ALREADY_SETTLED"
    )


# ----------------------------------------------------------------------
# What the operator UI asks for
# ----------------------------------------------------------------------

def test_next_session_reports_where_the_day_got_to(client, registered_animal):
    response = client.get(
        f"/farm/milk/next-session?operational_date={TODAY.isoformat()}"
    )
    assert response.status_code == 200
    assert response.json()["next_session"] == "MORNING"

    _record_milk(client, registered_animal, "MORNING", morning_yield=9.0)

    body = client.get(
        f"/farm/milk/next-session?operational_date={TODAY.isoformat()}"
    ).json()

    assert body["next_session"] == "EVENING"
    assert body["sequencing_active"] is True
    assert body["settled_sessions"][0]["milking_session"] == "MORNING"


# ----------------------------------------------------------------------
# G1.6: NULL is not zero
# ----------------------------------------------------------------------

def test_an_unentered_session_stays_null(client, registered_animal):
    _record_milk(client, registered_animal, "MORNING", morning_yield=9.0)

    row = _milk_rows(registered_animal)[0]

    assert row.morning_yield == 9.0
    assert row.afternoon_yield is None
    assert row.evening_yield is None


def test_an_entered_zero_is_recorded_as_zero(client, registered_animal):
    _record_milk(client, registered_animal, "MORNING", morning_yield=0.0)

    row = _milk_rows(registered_animal)[0]

    assert row.morning_yield == 0.0
    assert row.evening_yield is None


# ----------------------------------------------------------------------
# One animal-day is one row
# ----------------------------------------------------------------------

def test_sessions_merge_into_one_animal_day_row(client, registered_animal):
    _record_milk(client, registered_animal, "MORNING", morning_yield=9.0)
    _record_milk(client, registered_animal, "EVENING", evening_yield=7.0)

    rows = _milk_rows(registered_animal)

    assert len(rows) == 1
    assert rows[0].morning_yield == 9.0
    assert rows[0].evening_yield == 7.0
    assert rows[0].total_yield == 16.0


def test_a_later_session_never_nulls_an_earlier_one(client, registered_animal):
    _record_milk(client, registered_animal, "MORNING", morning_yield=9.0)
    _record_milk(client, registered_animal, "EVENING", evening_yield=7.0)

    assert _milk_rows(registered_animal)[0].morning_yield == 9.0


# ----------------------------------------------------------------------
# The withdrawal interlock survives all of the above
# ----------------------------------------------------------------------

def test_treatment_does_not_change_milk_entry_status(
    client, registered_animal
):
    treatment_response = client.post(
        "/farm/treatments",
        json={
            "animal_id": registered_animal,
            "medicine": "Penicillin",
            "milk_withdrawal_days": 4,
            "operator": "Vet",
        },
    )

    assert treatment_response.status_code == 200

    morning = _record_milk(
        client,
        registered_animal,
        "MORNING",
        morning_yield=9.0,
    )

    assert morning.status_code == 200
    assert morning.json()["status"] == "RECORDED"
    assert morning.json().get("withdrawal_warning") in {False, None}

    evening = _record_milk(
        client,
        registered_animal,
        "EVENING",
        evening_yield=7.0,
    )

    assert evening.status_code == 200
    assert evening.json()["status"] == "RECORDED"

    row = _milk_rows(registered_animal)[0]
    assert row.status == "RECORDED"
    assert row.morning_yield == 9.0
    assert row.evening_yield == 7.0
    assert row.total_yield == 16.0

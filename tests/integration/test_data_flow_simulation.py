"""Entry-point-driven data-flow simulations.

These tests deliberately write through the public farm entry points instead
of inserting domain rows directly.  The purpose is to catch the class of
failures where tests pass while an operator's real entry point writes data to
an orphaned projection, an alternate repository, or a mismatched calculation.
"""


def test_milk_entry_flows_to_animal_passport_and_operations_dashboard(
    client,
    registered_animal,
):
    """A real milk entry must survive every required read boundary.

    The simulation enters only a morning value.  The resulting record must
    therefore contain that asserted value and must not fabricate afternoon or
    evening production.
    """
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "operator": "simulation",
        },
    )
    assert response.status_code == 200, response.text

    entry = response.json()
    assert entry["animal_id"] == registered_animal
    assert entry["milking_session"] == "MORNING"
    assert entry["morning_yield"] == 8.0
    assert entry["total_yield"] == 8.0
    assert entry.get("afternoon_yield") is None
    assert entry.get("evening_yield") is None

    passport = client.get(
        f"/farm/animals/{registered_animal}/passport"
    )
    assert passport.status_code == 200, passport.text
    passport_body = passport.json()

    milk_rows = passport_body["history"]["milk"]
    matching = [
        row
        for row in milk_rows
        if row["animal_id"] == registered_animal
        and row["milking_session"] == "MORNING"
        and row["total_yield"] == 8.0
    ]
    assert matching, passport_body

    lifetime = passport_body["production"]["lifetime"]
    assert lifetime["lifetime_milk_liters"] == 8.0
    assert lifetime["peak_daily_yield_liters"] == 8.0

    operations = client.get("/operations/dashboard")
    assert operations.status_code == 200, operations.text
    operations_body = operations.json()
    assert operations_body["milk_today"] == 8.0


def test_milk_entry_simulation_does_not_invent_unentered_sessions(
    client,
    registered_animal,
):
    """Explicit zero is different from an omitted session value."""
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "afternoon_yield": 0.0,
            "milking_session": "AFTERNOON",
            "operator": "simulation",
        },
    )
    assert response.status_code == 200, response.text

    entry = response.json()
    assert entry["afternoon_yield"] == 0.0
    assert entry["total_yield"] == 0.0
    assert entry.get("morning_yield") is None
    assert entry.get("evening_yield") is None

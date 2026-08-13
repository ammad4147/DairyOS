def test_lifetime_animal_passport_aggregates_persisted_history(
    client,
    registered_animal,
):
    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "operator": "Milking Operator",
        },
    )

    assert milk.status_code == 200, milk.text

    passport = client.get(
        f"/farm/animals/{registered_animal}/passport"
    )

    assert passport.status_code == 200, passport.text

    data = passport.json()

    # Authoritative Lifetime Animal Passport contract.
    assert data["animal"]["animal_id"] == registered_animal

    assert "history" in data
    assert "milk" in data["history"]
    assert len(data["history"]["milk"]) >= 1

    milk_record = data["history"]["milk"][0]

    assert milk_record["animal_id"] == registered_animal
    assert milk_record["milking_session"] == "MORNING"
    assert milk_record["total_yield"] == 8.0

    assert data["record_counts"]["milk"] >= 1

    assert "timeline" in data
    assert any(
        item["domain"] == "milk"
        for item in data["timeline"]
    )


def test_lifetime_animal_passport_returns_404_for_unknown_animal(
    client,
):
    response = client.get(
        "/farm/animals/AN-DOES-NOT-EXIST/passport"
    )

    assert response.status_code == 404

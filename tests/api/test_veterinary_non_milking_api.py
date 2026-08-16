from datetime import datetime, timedelta, timezone


def _directive(client, animal_id, directive, **kwargs):
    payload = {
        "directive": directive,
        "changed_by": "Dr Vet",
        "reason": "Veterinary instruction",
    }
    payload.update(kwargs)

    return client.post(
        f"/farm/animals/{animal_id}/non-milking-directive",
        json=payload,
    )


def test_temporary_non_milking_moves_animal_out_of_milking_herd(
    client,
    registered_animal,
):
    response = _directive(
        client,
        registered_animal,
        "TEMPORARY_NON_MILKING",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["directive"] == "TEMPORARY_NON_MILKING"
    assert body["lifecycle_status"] == "DRY"
    assert body["is_currently_milking"] is False
    assert body["milk_expected"] is False

    milking = client.get(
        "/farm/animals/current/milking"
    )

    assert milking.status_code == 200
    assert registered_animal not in {
        row["animal_id"]
        for row in milking.json()
    }


def test_permanent_non_milking_has_zero_expected_milk(
    client,
    registered_animal,
):
    response = _directive(
        client,
        registered_animal,
        "PERMANENT_NON_MILKING",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["directive"] == "PERMANENT_NON_MILKING"
    assert body["lifecycle_status"] == "DRY"
    assert body["is_currently_milking"] is False
    assert body["milk_expected"] is False


def test_milk_separately_is_not_active_milking_but_milk_is_expected(
    client,
    registered_animal,
):
    response = _directive(
        client,
        registered_animal,
        "MILK_SEPARATELY",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["directive"] == "MILK_SEPARATELY"
    assert body["lifecycle_status"] == "DRY"
    assert body["is_currently_milking"] is False
    assert body["milk_expected"] is True


def test_temporary_directive_can_carry_effective_until(
    client,
    registered_animal,
):
    until = (
        datetime.now(timezone.utc)
        + timedelta(days=5)
    ).isoformat()

    response = _directive(
        client,
        registered_animal,
        "TEMPORARY_NON_MILKING",
        effective_until=until,
    )

    assert response.status_code == 200
    assert response.json()["non_milking_until"] is not None


def test_clear_restores_previous_milking_state(
    client,
    registered_animal,
):
    applied = _directive(
        client,
        registered_animal,
        "TEMPORARY_NON_MILKING",
    )

    assert applied.status_code == 200

    cleared = _directive(
        client,
        registered_animal,
        "NONE",
    )

    assert cleared.status_code == 200

    body = cleared.json()

    assert body["status"] == "CLEARED"
    assert body["directive"] == "NONE"
    assert body["lifecycle_status"] == "LACTATING"
    assert body["is_currently_milking"] is True
    assert body["milk_expected"] is True


def test_unknown_animal_is_rejected(client):
    response = _directive(
        client,
        "NOT-A-REAL-ANIMAL",
        "TEMPORARY_NON_MILKING",
    )

    assert response.status_code == 404


def test_treatment_id_is_trace_reference_only(
    client,
    registered_animal,
):
    response = _directive(
        client,
        registered_animal,
        "MILK_SEPARATELY",
        treatment_id=987654,
    )

    assert response.status_code == 200
    assert response.json()["treatment_id"] == 987654

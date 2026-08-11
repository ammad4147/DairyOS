from dairyos.app import app


def test_reject_treatment_for_unknown_drug_without_override(client):
    """
    Tier 1a safety contract: an unknown medicine with no explicit
    withdrawal days must be rejected, never silently recorded with a
    zero-day (unsafe) withdrawal period.
    """
    response = client.post(
        "/farm/treatments",
        json={
            "animal_id": "TEST-WD-001",
            "medicine": "Totally-Unlisted-Drug-XYZ",
            "diagnosis": "Mastitis",
            "operator": "Dr Vet",
        },
    )

    assert response.status_code == 400
    assert "Unknown medicine" in response.json()["detail"]


def test_record_treatment_with_explicit_withdrawal_days(client):
    response = client.post(
        "/farm/treatments",
        json={
            "animal_id": "TEST-WD-002",
            "medicine": "Manual-Override-Drug",
            "diagnosis": "Mastitis",
            "milk_withdrawal_days": 4,
            "treated_by": "Dr Vet",
            "operator": "Dr Vet",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["animal_id"] == "TEST-WD-002"
    assert body["milk_withdrawal_days"] == 4
    assert body["withdrawal_source"] == "manual_override"
    assert body["milk_withdrawal_until"]
    assert body["treatment_id"]


def test_treatment_opens_active_withdrawal_and_blocks_milk_entry(client):
    animal_id = "TEST-WD-003"

    treatment_response = client.post(
        "/farm/treatments",
        json={
            "animal_id": animal_id,
            "medicine": "Blocking-Drug",
            "diagnosis": "Respiratory infection",
            "milk_withdrawal_days": 5,
            "operator": "Dr Vet",
        },
    )
    assert treatment_response.status_code == 200

    active = client.get("/farm/withdrawals/active")
    assert active.status_code == 200
    active_ids = [row["animal_id"] for row in active.json()]
    assert animal_id in active_ids

    milk_response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "morning_yield": 8.0,
            "operator": "Milking Operator",
        },
    )

    assert milk_response.status_code == 200
    milk_body = milk_response.json()
    assert milk_body["status"] == "WITHHELD"
    assert milk_body["withdrawal_warning"] is True
    assert "SAFETY ALERT" in milk_body["safety_message"]


def test_milk_entry_not_blocked_for_untreated_animal(client):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": "TEST-WD-004-CLEAN",
            "morning_yield": 6.0,
            "operator": "Milking Operator",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RECORDED"
    assert body["withdrawal_warning"] is False


def test_list_treatments(client):
    client.post(
        "/farm/treatments",
        json={
            "animal_id": "TEST-WD-005",
            "medicine": "List-Test-Drug",
            "milk_withdrawal_days": 2,
            "operator": "Dr Vet",
        },
    )

    response = client.get("/farm/treatments")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_negative_withdrawal_days_rejected(client):
    response = client.post(
        "/farm/treatments",
        json={
            "animal_id": "TEST-WD-006",
            "medicine": "Negative-Days-Drug",
            "milk_withdrawal_days": -1,
            "operator": "Dr Vet",
        },
    )

    assert response.status_code == 400


def test_drug_reference_upsert_and_list(client):
    create_response = client.post(
        "/farm/drug-reference",
        json={
            "medicine": "Reference-Test-Drug",
            "milk_withdrawal_days": 3,
            "meat_withdrawal_days": 10,
            "notes": "Test entry",
            "verified": True,
            "operator": "Farm Manager",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["medicine"] == "Reference-Test-Drug"
    assert created["milk_withdrawal_days"] == 3
    assert created["verified"] is True

    list_response = client.get("/farm/drug-reference")
    assert list_response.status_code == 200
    names = [row["medicine"] for row in list_response.json()]
    assert "Reference-Test-Drug" in names


def test_treatment_uses_drug_reference_table_when_medicine_known(client):
    client.post(
        "/farm/drug-reference",
        json={
            "medicine": "Known-Reference-Drug",
            "milk_withdrawal_days": 6,
            "operator": "Farm Manager",
        },
    )

    response = client.post(
        "/farm/treatments",
        json={
            "animal_id": "TEST-WD-007",
            "medicine": "known-reference-drug",  # case-insensitive match
            "operator": "Dr Vet",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["milk_withdrawal_days"] == 6
    assert body["withdrawal_source"] == "reference_table"


def test_treatment_override_only_extends_reference_period(client):
    client.post(
        "/farm/drug-reference",
        json={
            "medicine": "Extend-Test-Drug",
            "milk_withdrawal_days": 3,
            "operator": "Farm Manager",
        },
    )

    # Attempt to SHORTEN below the reference value -- must not be honored.
    shorten_response = client.post(
        "/farm/treatments",
        json={
            "animal_id": "TEST-WD-008",
            "medicine": "Extend-Test-Drug",
            "milk_withdrawal_days": 1,
            "operator": "Dr Vet",
        },
    )
    assert shorten_response.status_code == 200
    assert shorten_response.json()["milk_withdrawal_days"] == 3

    # Extending it further IS honored.
    extend_response = client.post(
        "/farm/treatments",
        json={
            "animal_id": "TEST-WD-009",
            "medicine": "Extend-Test-Drug",
            "milk_withdrawal_days": 10,
            "operator": "Dr Vet",
        },
    )
    assert extend_response.status_code == 200
    body = extend_response.json()
    assert body["milk_withdrawal_days"] == 10
    assert body["withdrawal_source"] == "override_extended"

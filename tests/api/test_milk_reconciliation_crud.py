from datetime import date, timedelta


def _record_three_sessions(client, animal_id: str, production_date: date):
    payloads = [
        ("MORNING", 10.0),
        ("AFTERNOON", 8.0),
        ("EVENING", 7.0),
    ]
    responses = []
    for session, litres in payloads:
        response = client.post(
            "/farm/milk",
            json={
                "animal_id": animal_id,
                "milking_session": session,
                "production_date": production_date.isoformat(),
                "morning_yield": litres if session == "MORNING" else None,
                "afternoon_yield": litres if session == "AFTERNOON" else None,
                "evening_yield": litres if session == "EVENING" else None,
                "operator": "TEST",
            },
        )
        assert response.status_code == 200, response.text
        responses.append(response.json())
    return responses


def test_milk_production_is_persisted_and_respects_animal_schedule(client, registered_animal):
    production_date = date.today()
    _record_three_sessions(client, registered_animal, production_date)

    ledger = client.get(
        "/farm/milk/ledger",
        params={"start_date": production_date, "end_date": production_date},
    )
    assert ledger.status_code == 200, ledger.text

    body = ledger.json()
    assert len(body["production"]) == 1
    row = body["production"][0]
    assert row["animal_id"] == registered_animal
    assert row["total_yield"] == 25.0
    assert row["status"] == "RECORDED"


def test_reconciliation_rejects_over_disposition_and_tracks_sold_and_non_sale(client, registered_animal):
    production_date = date.today() - timedelta(days=1)
    _record_three_sessions(client, registered_animal, production_date)

    sold = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": production_date.isoformat(),
            "disposition_type": "SOLD",
            "quantity_litres": 15,
            "sale_id": "TEST-SALE-001",
            "counterparty": "Test Buyer",
            "selling_price_per_litre": 225,
        },
    )
    assert sold.status_code == 200, sold.text

    calf = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": production_date.isoformat(),
            "disposition_type": "CALF_FEED",
            "quantity_litres": 10,
        },
    )
    assert calf.status_code == 200, calf.text

    over = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": production_date.isoformat(),
            "disposition_type": "WASTAGE",
            "quantity_litres": 0.1,
        },
    )
    assert over.status_code == 422, over.text

    reconciliation = client.get(
        "/farm/milk/reconciliation",
        params={"production_date": production_date},
    )
    assert reconciliation.status_code == 200, reconciliation.text
    body = reconciliation.json()
    assert body["produced_litres"] == 25.0
    assert body["sold_litres"] == 15.0
    assert body["non_sale_accounted_litres"] == 10.0
    assert body["unaccounted_litres"] == 0.0
    assert body["over_accounted_litres"] == 0.0
    assert body["status"] == "RECONCILED"


def test_production_edit_changes_total_and_preserves_animal_identity(client, registered_animal):
    production_date = date.today() - timedelta(days=2)
    _record_three_sessions(client, registered_animal, production_date)

    ledger = client.get(
        "/farm/milk/ledger",
        params={"start_date": production_date, "end_date": production_date},
    )
    record = ledger.json()["production"][0]

    response = client.patch(
        f"/farm/milk/production/{record['id']}",
        json={
            "production_date": production_date.isoformat(),
            "morning_yield": 12.0,
            "afternoon_yield": 8.0,
            "evening_yield": 7.0,
            "notes": "Corrected morning reading",
        },
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["animal_id"] == registered_animal
    assert updated["total_yield"] == 27.0
    assert updated["notes"] == "Corrected morning reading"


def test_void_production_is_auditable_and_removes_it_from_current_reconciliation(client, registered_animal):
    production_date = date.today() - timedelta(days=3)
    _record_three_sessions(client, registered_animal, production_date)

    ledger = client.get(
        "/farm/milk/ledger",
        params={"start_date": production_date, "end_date": production_date},
    )
    record = ledger.json()["production"][0]

    response = client.post(
        f"/farm/milk/production/{record['id']}/void",
        json={"reason": "Duplicate operator entry"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "VOID"

    ledger_after = client.get(
        "/farm/milk/ledger",
        params={"start_date": production_date, "end_date": production_date},
    )
    rows = ledger_after.json()["production"]
    assert len(rows) == 1
    assert rows[0]["status"] == "VOID"

    reconciliation = client.get(
        "/farm/milk/reconciliation",
        params={"production_date": production_date},
    )
    assert reconciliation.status_code == 200, reconciliation.text
    assert reconciliation.json()["production_complete"] is False


def test_disposition_edit_and_void_are_auditable(client, registered_animal):
    production_date = date.today() - timedelta(days=4)
    _record_three_sessions(client, registered_animal, production_date)

    created = client.post(
        "/farm/milk/dispositions",
        json={
            "production_date": production_date.isoformat(),
            "disposition_type": "SOLD",
            "quantity_litres": 10,
            "sale_id": "TEST-SALE-002",
            "counterparty": "Buyer A",
            "selling_price_per_litre": 220,
        },
    )
    assert created.status_code == 200, created.text
    disposition_id = created.json()["id"]

    updated = client.patch(
        f"/farm/milk/dispositions/{disposition_id}",
        json={
            "production_date": production_date.isoformat(),
            "quantity_litres": 12,
            "counterparty": "Buyer B",
            "selling_price_per_litre": 225,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["quantity_litres"] == 12.0
    assert updated.json()["amount_due"] == 2700.0

    voided = client.post(
        f"/farm/milk/dispositions/{disposition_id}/void",
        json={"reason": "Incorrect customer"},
    )
    assert voided.status_code == 200, voided.text
    assert voided.json()["status"] == "VOID"
    assert voided.json()["quantity_litres"] == 0.0

    reconciliation = client.get(
        "/farm/milk/reconciliation",
        params={"production_date": production_date},
    )
    assert reconciliation.status_code == 200, reconciliation.text
    assert reconciliation.json()["sold_litres"] == 0.0


def test_next_session_is_driven_by_animal_passport_frequency(client, registered_animal):
    target = date.today() - timedelta(days=5)
    result = client.get(
        "/farm/milk/next-session",
        params={"animal_id": registered_animal, "operational_date": target},
    )
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["milking_frequency"] == "THRICE_DAILY"
    assert body["expected_sessions"] == ["MORNING", "AFTERNOON", "EVENING"]

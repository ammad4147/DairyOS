"""Named human sessions remain the source of milk audit attribution."""

from datetime import UTC, datetime, timedelta

import pytest

from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.human_identity import HumanIdentity, HumanSession
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.repositories.repository_factory import RepositoryFactory


def _login(client, identity_id, pin):
    response = client.post(
        "/human-access/login", json={"identity_id": identity_id, "pin": pin}
    )
    assert response.status_code == 200, response.text
    return {"X-DairyOS-Human-Session": response.json()["session_token"]}


def _clear_test_human_access(factory):
    for model in (HumanSession, HumanIdentity):
        for row in factory.session.query(model).all():
            factory.session.delete(row)
            factory.session.flush()
    factory.session.commit()


@pytest.fixture
def isolated_human_access():
    factory = RepositoryFactory.create()
    try:
        _clear_test_human_access(factory)
    finally:
        factory.close()
    yield
    factory = RepositoryFactory.create()
    try:
        _clear_test_human_access(factory)
    finally:
        factory.close()


def test_milk_and_session_ledger_use_authenticated_human_names_for_two_roles(
    client, registered_animal
):
    bootstrap = client.post(
        "/human-access/bootstrap",
        json={
            "display_name": "Named Milk Admin",
            "pin": "4826",
            "pin_confirmation": "4826",
        },
    )
    assert bootstrap.status_code == 200, bootstrap.text
    admin_id = bootstrap.json()["id"]
    admin_headers = _login(client, admin_id, "4826")

    created = client.post(
        "/human-access/people",
        headers=admin_headers,
        json={"display_name": "Named Milker", "entry_group": "MILK_OPERATOR"},
    )
    assert created.status_code == 200, created.text
    milker_id = created.json()["id"]
    initialized = client.post(
        f"/human-access/people/{milker_id}/pin/initial",
        headers=admin_headers,
        json={"pin": "6382", "pin_confirmation": "6382"},
    )
    assert initialized.status_code == 200, initialized.text
    milker_headers = _login(client, milker_id, "6382")

    def record(headers, session, field):
        response = client.post(
            "/farm/milk",
            headers=headers,
            json={
                "animal_id": registered_animal,
                "milking_session": session,
                "production_date": "2026-08-13",
                field: 7.5,
                "operator": "WEB",
            },
        )
        assert response.status_code == 200, response.text

    record(admin_headers, "MORNING", "morning_yield")
    record(admin_headers, "AFTERNOON", "afternoon_yield")
    record(milker_headers, "EVENING", "evening_yield")

    factory = RepositoryFactory.create()
    try:
        records = (
            factory.session.query(HumanIdentity)
            .filter(HumanIdentity.id.in_([admin_id, milker_id]))
            .all()
        )
        assert {identity.id: identity.display_name for identity in records} == {
            admin_id: "Named Milk Admin",
            milker_id: "Named Milker",
        }
        ledger = factory.milking_session_ledger().get_all()
        by_session = {row.milking_session: row.recorded_by for row in ledger}
        assert by_session["MORNING"] == "Named Milk Admin"
        assert by_session["AFTERNOON"] == "Named Milk Admin"
        assert by_session["EVENING"] == "Named Milker"
        milk_events = (
            factory.session.query(EventJournalModel)
            .filter(EventJournalModel.event_type == "OperationalInputReceived")
            .all()
        )
        actors = {
            row.payload["milking_session"]: row.payload["operator"]
            for row in milk_events
            if row.payload.get("milking_session")
            and any(
                row.payload.get(field) is not None
                for field in ("morning_yield", "afternoon_yield", "evening_yield")
            )
        }
        assert actors["MORNING"] == "Named Milk Admin"
        assert actors["EVENING"] == "Named Milker"
    finally:
        factory.close()


def test_milk_disposition_ignores_spoofed_recorded_by_for_two_roles(
    client, registered_animal, isolated_human_access
):
    bootstrap = client.post(
        "/human-access/bootstrap",
        json={
            "display_name": "Disposition Admin",
            "pin": "4826",
            "pin_confirmation": "4826",
        },
    )
    assert bootstrap.status_code == 200, bootstrap.text
    admin_id = bootstrap.json()["id"]
    admin_headers = _login(client, admin_id, "4826")

    created = client.post(
        "/human-access/people",
        headers=admin_headers,
        json={"display_name": "Disposition Milker", "entry_group": "MILK_OPERATOR"},
    )
    assert created.status_code == 200, created.text
    milker_id = created.json()["id"]
    initialized = client.post(
        f"/human-access/people/{milker_id}/pin/initial",
        headers=admin_headers,
        json={"pin": "6382", "pin_confirmation": "6382"},
    )
    assert initialized.status_code == 200, initialized.text
    milker_headers = _login(client, milker_id, "6382")

    today = datetime.now(UTC).date()
    production_dates = [today - timedelta(days=2), today - timedelta(days=1)]
    actors = (
        (admin_headers, "Disposition Admin", production_dates[0], "DISP-AUDIT-ADMIN"),
        (milker_headers, "Disposition Milker", production_dates[1], "DISP-AUDIT-MILKER"),
    )
    for headers, _actor, production_date, sale_id in actors:
        milk = client.post(
            "/farm/milk",
            headers=headers,
            json={
                "animal_id": registered_animal,
                "milking_session": "MORNING",
                "production_date": production_date.isoformat(),
                "morning_yield": 12.0,
                "operator": "WEB",
            },
        )
        assert milk.status_code == 200, milk.text
        disposition = client.post(
            "/farm/milk/dispositions",
            headers=headers,
            json={
                "production_date": production_date.isoformat(),
                "disposition_type": "SOLD",
                "quantity_litres": 3.0,
                "sale_id": sale_id,
                "counterparty": "Test Buyer",
                "selling_price_per_litre": 100,
                "recorded_by": "SPOOFED WEB",
                "operator": "WEB",
            },
        )
        assert disposition.status_code == 200, disposition.text

    factory = RepositoryFactory.create()
    try:
        dispositions = (
            factory.session.query(MilkDisposition)
            .filter(MilkDisposition.sale_id.in_([item[3] for item in actors]))
            .all()
        )
        assert {row.sale_id: row.recorded_by for row in dispositions} == {
            "DISP-AUDIT-ADMIN": "Disposition Admin",
            "DISP-AUDIT-MILKER": "Disposition Milker",
        }

        events = (
            factory.session.query(EventJournalModel)
            .filter(EventJournalModel.event_type == "OperationalInputReceived")
            .all()
        )
        disposition_actors = {
            row.payload.get("sale_id"): row.payload.get("actor")
            for row in events
            if row.payload.get("input_type") == "milk_disposition"
            and row.payload.get("sale_id") in {item[3] for item in actors}
        }
        assert disposition_actors == {
            "DISP-AUDIT-ADMIN": "Disposition Admin",
            "DISP-AUDIT-MILKER": "Disposition Milker",
        }
    finally:
        factory.close()

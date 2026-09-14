from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from dairyos.app import container
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.operational_write import (
    OperationalProjectionOutbox,
    OperationalWrite,
)
from dairyos.data.models.vaccination_record import VaccinationRecord
from dairyos.data.repositories.vaccination_repository import VaccinationRepository

from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from tests.helpers.breeding import post_breeding


def _operational_today():
    return OperationalDateAuthority().current_date()


def _animal(client, ear_tag):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Heifer",
            "ear_tag": ear_tag,
            "breed": "Sahiwal",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def test_open_health_case_is_live_on_dashboard(client):
    animal_id = _animal(client, "DASH-HEALTH-OPEN-001")
    health_case = client.post(
        "/farm/health-cases",
        json={
            "animal_id": animal_id,
            "diagnosis": "Mastitis",
            "severity": "SEVERE",
            "operator": "AUDIT-VET",
        },
    )
    assert health_case.status_code == 200, health_case.text
    assert health_case.json()["status"] == "OPEN"

    observation = client.post(
        "/farm/health-observations",
        json={
            "animal_id": animal_id,
            "observation": "Clinical mastitis suspected",
            "severity": "SEVERE",
            "health_case_id": health_case.json()["id"],
            "operator": "AUDIT-VET",
        },
    )
    assert observation.status_code == 200, observation.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    health = dashboard.json()["health"]
    assert health["sick"] >= 1
    assert health["mastitis"] >= 1
    assert health["openCases"] >= 1
    sick_animals = [
        row for row in health["sick_animals"]
        if row["animal_id"] == animal_id
    ]
    assert len(sick_animals) == 1
    assert sick_animals[0]["diagnosis"] == "Mastitis"
    assert health["data_status"] == "LIVE_PERSISTED_DATA"


def test_insemination_is_live_on_dashboard(client):
    animal_id = _animal(client, "DASH-BREEDING-AI-001")
    response = post_breeding(
        client,
        animal_id,
        "insemination",
        "COMPLETED",
        technician="AUDIT-TECH",
        timestamp=datetime.now(UTC).date().isoformat(),
        operator="AUDIT-TECH",
    )
    assert response.status_code == 200, response.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    reproduction = dashboard.json()["reproduction"]
    assert reproduction["inseminated"] >= 1
    assert reproduction["pregnancyRatio"] == 0.0
    assert (
        reproduction["pregnancy_ratio_percent"]
        == reproduction["pregnancyRatio"]
    )
    assert reproduction["data_status"] == "LIVE_PERSISTED_DATA"


def _vaccination_rows_for_animal(dashboard_payload, animal_id):
    return [
        row
        for row in dashboard_payload["vaccination"]["due_animals"]
        if row["animal_id"] == animal_id
    ]


def test_unadministered_vaccination_due_today_is_live_on_dashboard(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-DUE-001")
    today = _operational_today()

    response = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "next_due_date": today.isoformat(),
            "schedule_status": "SCHEDULED",
            "batch_number": "FMD-DUE-001",
            "veterinarian": "AUDIT-VET",
            "operator": "AUDIT-VET",
        },
    )
    assert response.status_code == 200, response.text
    occurrence = response.json()
    assert occurrence["administered_date"] is None

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text

    payload = dashboard.json()
    health = payload["health"]
    rows = _vaccination_rows_for_animal(payload, animal_id)

    assert health["dueVax"] >= 1
    assert health["due_vaccinations"] == health["dueVax"]
    assert len(rows) == 1
    assert rows[0]["vaccination_occurrence_id"] == occurrence["id"]
    assert rows[0]["next_due_date"] == today.isoformat()
    assert rows[0]["due_state"] == "DUE_TODAY"
    assert health["data_status"] == "LIVE_PERSISTED_DATA"


def test_administered_vaccination_is_not_due_on_dashboard(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-GIVEN-001")
    today = _operational_today()

    response = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "administered_date": today.isoformat(),
            "next_due_date": today.isoformat(),
            "batch_number": "FMD-GIVEN-001",
            "veterinarian": "AUDIT-VET",
            "operator": "AUDIT-VET",
        },
    )
    assert response.status_code == 200, response.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text

    payload = dashboard.json()
    health = payload["health"]

    assert health["completedVax"] >= 1
    assert health["completed_vaccinations"] == health["completedVax"]
    assert _vaccination_rows_for_animal(payload, animal_id) == []


def test_administering_schedule_updates_same_occurrence_and_clears_dashboard(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-ENDORSE-001")
    today = _operational_today()

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "next_due_date": today.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    occurrence = scheduled.json()
    occurrence_id = occurrence["id"]
    assert occurrence["administered_date"] is None

    before = client.get("/dashboard")
    assert before.status_code == 200, before.text
    before_rows = _vaccination_rows_for_animal(
        before.json(),
        animal_id,
    )
    assert len(before_rows) == 1
    assert before_rows[0]["vaccination_occurrence_id"] == occurrence_id
    assert before_rows[0]["due_state"] == "DUE_TODAY"

    given = client.post(
        (
            f"/farm/animals/{animal_id}/vaccinations/"
            f"{occurrence_id}/administer"
        ),
        json={
            "administered_date": today.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert given.status_code == 200, given.text

    administered = given.json()
    assert administered["id"] == occurrence_id
    assert administered["administered_date"] == today.isoformat()
    assert administered["next_due_date"] == today.isoformat()
    assert administered["schedule_status"] == "ADMINISTERED"

    history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert history.status_code == 200, history.text

    same_occurrence = [
        row
        for row in history.json()
        if row.get("id") == occurrence_id
    ]
    assert len(same_occurrence) == 1
    assert same_occurrence[0]["administered_date"] == today.isoformat()
    assert same_occurrence[0]["next_due_date"] == today.isoformat()

    after = client.get("/dashboard")
    assert after.status_code == 200, after.text
    assert _vaccination_rows_for_animal(
        after.json(),
        animal_id,
    ) == []


def test_vaccination_occurrence_cannot_be_administered_twice(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-TWICE-001")
    today = _operational_today()

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "next_due_date": today.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    occurrence_id = scheduled.json()["id"]

    endpoint = (
        f"/farm/animals/{animal_id}/vaccinations/"
        f"{occurrence_id}/administer"
    )

    first = client.post(
        endpoint,
        json={
            "administered_date": today.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert first.status_code == 200, first.text

    second = client.post(
        endpoint,
        json={
            "administered_date": today.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert second.status_code == 409, second.text


def test_vaccination_occurrence_rejects_cross_animal_administration(client):
    first_animal = _animal(
        client,
        "DASH-HEALTH-VAX-OWNER-001",
    )
    second_animal = _animal(
        client,
        "DASH-HEALTH-VAX-OTHER-001",
    )
    today = _operational_today()

    scheduled = client.post(
        f"/farm/animals/{first_animal}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "next_due_date": today.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    occurrence_id = scheduled.json()["id"]

    response = client.post(
        (
            f"/farm/animals/{second_animal}/vaccinations/"
            f"{occurrence_id}/administer"
        ),
        json={
            "administered_date": today.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert response.status_code == 409, response.text


def test_multiple_vaccination_occurrences_are_independent(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-MULTI-001")
    today = _operational_today()
    future_due = today + timedelta(days=30)

    due_today = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 1",
            "next_due_date": today.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert due_today.status_code == 200, due_today.text

    future = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 2",
            "next_due_date": future_due.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert future.status_code == 200, future.text

    first_id = due_today.json()["id"]
    second_id = future.json()["id"]

    assert first_id != second_id

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text

    rows = _vaccination_rows_for_animal(
        dashboard.json(),
        animal_id,
    )

    assert len(rows) == 1
    assert rows[0]["vaccination_occurrence_id"] == first_id
    assert rows[0]["due_state"] == "DUE_TODAY"

    administered = client.post(
        (
            f"/farm/animals/{animal_id}/vaccinations/"
            f"{first_id}/administer"
        ),
        json={
            "administered_date": today.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert administered.status_code == 200, administered.text

    history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert history.status_code == 200, history.text

    relational = [
        row
        for row in history.json()
        if row.get("id") in {first_id, second_id}
    ]

    assert len(relational) == 2

    first_row = next(
        row for row in relational
        if row["id"] == first_id
    )
    second_row = next(
        row for row in relational
        if row["id"] == second_id
    )

    assert first_row["administered_date"] == today.isoformat()
    assert first_row["next_due_date"] == today.isoformat()

    assert second_row["administered_date"] is None
    assert second_row["next_due_date"] == future_due.isoformat()

    after = client.get("/dashboard")
    assert after.status_code == 200, after.text
    assert _vaccination_rows_for_animal(
        after.json(),
        animal_id,
    ) == []


def test_overdue_unadministered_vaccination_is_live_on_dashboard(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-OVERDUE-001")
    today = _operational_today()
    overdue_date = today - timedelta(days=1)

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "HS",
            "dose": "2 ml",
            "next_due_date": overdue_date.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text

    rows = _vaccination_rows_for_animal(
        dashboard.json(),
        animal_id,
    )

    assert len(rows) == 1
    assert rows[0]["vaccination_occurrence_id"] == scheduled.json()["id"]
    assert rows[0]["next_due_date"] == overdue_date.isoformat()
    assert rows[0]["due_state"] == "OVERDUE"


def test_future_vaccination_is_not_dashboard_attention(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-FUTURE-001")
    today = _operational_today()
    future_due = today + timedelta(days=10)

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "BQ",
            "dose": "2 ml",
            "next_due_date": future_due.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text

    assert _vaccination_rows_for_animal(
        dashboard.json(),
        animal_id,
    ) == []


def test_administered_date_retains_distinct_scheduled_date(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-LATE-001")
    today = _operational_today()
    scheduled_date = today - timedelta(days=2)

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "next_due_date": scheduled_date.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    occurrence_id = scheduled.json()["id"]

    given = client.post(
        (
            f"/farm/animals/{animal_id}/vaccinations/"
            f"{occurrence_id}/administer"
        ),
        json={
            "administered_date": today.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert given.status_code == 200, given.text

    row = given.json()
    assert row["id"] == occurrence_id
    assert row["next_due_date"] == scheduled_date.isoformat()
    assert row["administered_date"] == today.isoformat()


def test_due_next_30_days_excludes_today_and_given_occurrences(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-30D-001")
    today = _operational_today()
    future_due = today + timedelta(days=10)

    due_today = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "2 ml",
            "next_due_date": today.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert due_today.status_code == 200, due_today.text

    future = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "HS",
            "dose": "2 ml",
            "next_due_date": future_due.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert future.status_code == 200, future.text

    given = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "BQ",
            "administered_date": today.isoformat(),
            "next_due_date": future_due.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert given.status_code == 200, given.text

    summary = client.get("/farm/vaccination/summary")
    assert summary.status_code == 200, summary.text

    payload = summary.json()

    # For this animal there is exactly one unresolved future occurrence
    # inside the next-30-day window. Due-today and administered rows do
    # not belong to this counter.
    upcoming = [
        row
        for row in payload["upcomingVaccinations"]
        if row["animal_id"] == animal_id
    ]

    assert len(upcoming) == 2

    future_rows = [
        row
        for row in upcoming
        if row["next_due_date"] == future_due.isoformat()
    ]
    assert len(future_rows) == 1
    assert future_rows[0]["vaccine"] == "HS"



def test_vaccination_administration_event_is_not_second_occurrence(client):
    animal_id = _animal(client, "DASH-HEALTH-VAX-AUDIT-001")
    today = _operational_today()

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 1",
            "next_due_date": today.isoformat(),
            "schedule_status": "SCHEDULED",
            "operator": "AUDIT-VET",
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    occurrence_id = scheduled.json()["id"]

    before_history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert before_history.status_code == 200, before_history.text

    before_rows = [
        row
        for row in before_history.json()
        if row.get("id") == occurrence_id
    ]
    assert len(before_rows) == 1

    before_dashboard = client.get("/dashboard")
    assert before_dashboard.status_code == 200, before_dashboard.text

    before_completed = before_dashboard.json()["health"]["completedVax"]

    administered = client.post(
        (
            f"/farm/animals/{animal_id}/vaccinations/"
            f"{occurrence_id}/administer"
        ),
        json={
            "administered_date": today.isoformat(),
            "operator": "AUDIT-VET",
        },
    )
    assert administered.status_code == 200, administered.text
    assert administered.json()["id"] == occurrence_id

    after_history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert after_history.status_code == 200, after_history.text

    history = after_history.json()

    same_occurrence = [
        row
        for row in history
        if row.get("id") == occurrence_id
    ]
    assert len(same_occurrence) == 1
    assert same_occurrence[0]["administered_date"] == today.isoformat()

    administration_audit_rows = [
        row
        for row in history
        if str(row.get("event_action") or "").upper()
        == "VACCINATION_ADMINISTERED"
    ]
    assert administration_audit_rows == []

    after_dashboard = client.get("/dashboard")
    assert after_dashboard.status_code == 200, after_dashboard.text

    payload = after_dashboard.json()

    assert (
        payload["health"]["completedVax"]
        == before_completed + 1
    )

    due_rows = [
        row
        for row in payload["vaccination"]["due_animals"]
        if row["animal_id"] == animal_id
    ]
    assert due_rows == []

def test_vaccination_schedule_batch_creates_multiple_occurrences_atomically(client):
    animal_id = _animal(client, "VAX-BATCH-01")

    response = client.post(
        f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
        json={
            "operator": "Batch Test",
            "occurrences": [
                {
                    "vaccine": "FMD",
                    "dose": "1",
                    "scheduled_date": "2026-09-14",
                    "veterinarian": "Vet A",
                },
                {
                    "vaccine": "FMD",
                    "dose": "2",
                    "scheduled_date": "2027-03-14",
                    "veterinarian": "Vet A",
                },
                {
                    "vaccine": "HS",
                    "dose": "1",
                    "scheduled_date": "2026-09-25",
                    "veterinarian": "Vet B",
                },
            ],
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert body["animal_id"] == animal_id
    assert body["count"] == 3
    assert len(body["occurrences"]) == 3

    history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert history.status_code == 200, history.text

    rows = [
        row
        for row in history.json()
        if row.get("id") is not None
    ]

    assert len(rows) == 3

    assert {
        (row["vaccine"], row["next_due_date"])
        for row in rows
    } == {
        ("FMD", "2026-09-14"),
        ("FMD", "2027-03-14"),
        ("HS", "2026-09-25"),
    }

    assert all(
        row["administered_date"] is None
        for row in rows
    )

    assert {
        (row["vaccine"], row["veterinarian"])
        for row in rows
    } == {
        ("FMD", "Vet A"),
        ("HS", "Vet B"),
    }


def test_vaccination_schedule_batch_rejects_duplicate_occurrence_without_partial_write(
    client,
):
    animal_id = _animal(client, "VAX-BATCH-02")

    before = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert before.status_code == 200, before.text

    response = client.post(
        f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
        json={
            "operator": "Batch Test",
            "occurrences": [
                {
                    "vaccine": "FMD",
                    "dose": "1",
                    "scheduled_date": "2026-09-20",
                },
                {
                    "vaccine": "FMD",
                    "dose": "duplicate",
                    "scheduled_date": "2026-09-20",
                },
                {
                    "vaccine": "HS",
                    "dose": "1",
                    "scheduled_date": "2026-09-21",
                },
            ],
        },
    )

    assert response.status_code == 409, response.text

    after = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert after.status_code == 200, after.text
    assert after.json() == before.json()


def test_vaccination_schedule_batch_validates_complete_request_before_writing(client):
    animal_id = _animal(client, "VAX-BATCH-03")

    response = client.post(
        f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
        json={
            "operator": "Batch Test",
            "occurrences": [
                {
                    "vaccine": "FMD",
                    "scheduled_date": "2026-09-20",
                },
                {
                    "vaccine": "",
                    "scheduled_date": "2026-09-21",
                },
            ],
        },
    )

    assert response.status_code == 422, response.text

    history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert history.status_code == 200, history.text
    assert history.json() == []


def test_vaccination_schedule_batch_rejects_empty_request(client):
    animal_id = _animal(client, "VAX-BATCH-04")

    response = client.post(
        f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
        json={
            "operator": "Batch Test",
            "occurrences": [],
        },
    )

    assert response.status_code == 422, response.text

    history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert history.status_code == 200, history.text
    assert history.json() == []


def test_vaccination_schedule_batch_rolls_back_after_first_occurrence_is_flushed(
    client,
    monkeypatch,
):
    animal_id = _animal(client, "VAX-BATCH-ROLLBACK-01")
    engine = container.repository_factory.session.get_bind()

    with Session(engine) as session:
        baseline = {
            "vaccinations": session.query(VaccinationRecord).count(),
            "journal": session.query(EventJournalModel).count(),
            "outbox": session.query(OperationalProjectionOutbox).count(),
            "writes": session.query(OperationalWrite).count(),
        }

    original_add = VaccinationRepository.add
    add_calls = 0

    def fail_on_second_add(self, record, *, commit=True):
        nonlocal add_calls
        add_calls += 1

        saved = original_add(self, record, commit=False)

        if add_calls == 2:
            raise RuntimeError(
                "injected vaccination batch failure after first occurrence event"
            )

        return saved

    monkeypatch.setattr(
        VaccinationRepository,
        "add",
        fail_on_second_add,
    )

    with pytest.raises(
        RuntimeError,
        match="injected vaccination batch failure after first occurrence event",
    ):
        client.post(
            f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
            json={
                "operator": "Rollback Test",
                "occurrences": [
                    {
                        "vaccine": "FMD",
                        "dose": "1",
                        "scheduled_date": "2026-09-20",
                        "veterinarian": "Vet Rollback",
                    },
                    {
                        "vaccine": "HS",
                        "dose": "1",
                        "scheduled_date": "2026-09-21",
                        "veterinarian": "Vet Rollback",
                    },
                ],
            },
        )

    assert add_calls == 2

    with Session(engine) as session:
        assert (
            session.query(VaccinationRecord).count()
            == baseline["vaccinations"]
        )
        assert (
            session.query(EventJournalModel).count()
            == baseline["journal"]
        )
        assert (
            session.query(OperationalProjectionOutbox).count()
            == baseline["outbox"]
        )
        assert (
            session.query(OperationalWrite).count()
            == baseline["writes"]
        )

        assert (
            session.query(VaccinationRecord)
            .filter(VaccinationRecord.animal_id == animal_id)
            .count()
            == 0
        )

def test_vaccination_audit_history_preserves_schedule_and_administration_events(
    client,
):
    animal_id = _animal(client, "VAX-AUDIT-01")

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
        json={
            "operator": "Audit Scheduler",
            "occurrences": [
                {
                    "vaccine": "FMD",
                    "dose": "1",
                    "scheduled_date": "2026-09-14",
                    "veterinarian": "Vet Schedule",
                    "notes": "Scheduled audit occurrence",
                }
            ],
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    occurrence_id = scheduled.json()["occurrences"][0]["id"]

    administered = client.post(
        f"/farm/animals/{animal_id}/vaccinations/{occurrence_id}/administer",
        json={
            "administered_date": "2026-09-14",
            "operator": "Audit Administrator",
            "veterinarian": "Vet Given",
            "notes": "Administration audit occurrence",
        },
    )
    assert administered.status_code == 200, administered.text

    response = client.get(
        "/farm/vaccinations/audit-history",
        params={"animal_id": animal_id},
    )
    assert response.status_code == 200, response.text

    rows = response.json()

    assert len(rows) == 2

    actions = [row["action"] for row in rows]
    assert set(actions) == {"SCHEDULE_CREATED", "ADMINISTERED"}

    scheduled_row = next(
        row for row in rows if row["action"] == "SCHEDULE_CREATED"
    )
    given_row = next(
        row for row in rows if row["action"] == "ADMINISTERED"
    )

    assert scheduled_row["animal_id"] == animal_id
    assert scheduled_row["vaccine"] == "FMD"
    assert scheduled_row["scheduled_date"] == "2026-09-14"
    assert scheduled_row["administered_date"] is None
    assert scheduled_row["event_id"]

    assert given_row["animal_id"] == animal_id
    assert given_row["vaccine"] == "FMD"
    assert given_row["vaccination_occurrence_id"] == occurrence_id
    assert given_row["scheduled_date"] == "2026-09-14"
    assert given_row["administered_date"] == "2026-09-14"
    assert given_row["event_id"]

    # The audit history must not create another vaccination occurrence.
    occurrence_history = client.get(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    assert occurrence_history.status_code == 200, occurrence_history.text

    relational_rows = [
        row
        for row in occurrence_history.json()
        if row.get("id") == occurrence_id
    ]
    assert len(relational_rows) == 1


def test_vaccination_schedule_can_be_amended_before_administration(client):
    animal_id = _animal(client, "VAX-AMEND-01")

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 1",
            "next_due_date": "2026-09-14",
            "schedule_status": "SCHEDULED",
            "veterinarian": "Original Vet",
            "notes": "Original note",
            "operator": "Audit Scheduler",
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    original = scheduled.json()
    occurrence_id = original["id"]
    created_at = original["created_at"]
    source_event_id = original["source_event_id"]

    amended = client.post(
        f"/farm/animals/{animal_id}/vaccinations/{occurrence_id}/amend",
        json={
            "vaccine": "HS",
            "dose": "Dose 2",
            "scheduled_date": "2026-09-21",
            "veterinarian": "Amending Vet",
            "notes": "Moved campaign",
            "operator": "Audit Amender",
        },
    )
    assert amended.status_code == 200, amended.text

    row = amended.json()
    assert row["id"] == occurrence_id
    assert row["animal_id"] == animal_id
    assert row["vaccine"] == "HS"
    assert row["dose"] == "Dose 2"
    assert row["next_due_date"] == "2026-09-21"
    assert row["veterinarian"] == "Amending Vet"
    assert row["notes"] == "Moved campaign"
    assert row["administered_date"] is None
    assert row["created_at"] == created_at
    assert row["source_event_id"] == source_event_id

    history = client.get(
        "/farm/vaccinations/audit-history",
        params={"animal_id": animal_id},
    )
    assert history.status_code == 200, history.text

    actions = [entry["action"] for entry in history.json()]
    assert "SCHEDULE_CREATED" in actions
    assert "SCHEDULE_AMENDED" in actions


def test_vaccination_schedule_rejects_amendment_after_administration(client):
    animal_id = _animal(client, "VAX-AMEND-GIVEN-01")

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 1",
            "next_due_date": "2026-09-14",
            "schedule_status": "SCHEDULED",
            "operator": "Audit Scheduler",
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    occurrence_id = scheduled.json()["id"]

    administered = client.post(
        f"/farm/animals/{animal_id}/vaccinations/{occurrence_id}/administer",
        json={
            "administered_date": "2026-09-14",
            "operator": "Audit Administrator",
        },
    )
    assert administered.status_code == 200, administered.text

    amended = client.post(
        f"/farm/animals/{animal_id}/vaccinations/{occurrence_id}/amend",
        json={
            "vaccine": "HS",
            "dose": "Dose 2",
            "scheduled_date": "2026-09-21",
            "operator": "Audit Amender",
        },
    )
    assert amended.status_code == 409, amended.text

    voided = client.post(
        f"/farm/animals/{animal_id}/vaccinations/{occurrence_id}/void",
        json={"operator": "Audit Amender"},
    )
    assert voided.status_code == 409, voided.text


def test_vaccination_schedule_logical_void_excludes_dashboard_and_records_audit(
    client,
):
    animal_id = _animal(client, "VAX-VOID-01")

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 1",
            "next_due_date": "2026-09-14",
            "schedule_status": "SCHEDULED",
            "operator": "Audit Scheduler",
        },
    )
    assert scheduled.status_code == 200, scheduled.text
    occurrence_id = scheduled.json()["id"]

    voided = client.post(
        f"/farm/animals/{animal_id}/vaccinations/{occurrence_id}/void",
        json={
            "operator": "Audit Voider",
            "notes": "Campaign cancelled",
        },
    )
    assert voided.status_code == 200, voided.text
    assert voided.json()["id"] == occurrence_id
    assert voided.json()["status"] == "VOID"

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    assert _vaccination_rows_for_animal(
        dashboard.json(),
        animal_id,
    ) == []

    history = client.get(
        "/farm/vaccinations/audit-history",
        params={"animal_id": animal_id},
    )
    assert history.status_code == 200, history.text

    actions = [entry["action"] for entry in history.json()]
    assert "SCHEDULE_CREATED" in actions
    assert "SCHEDULE_VOIDED" in actions


def test_vaccination_schedule_rejects_duplicate_active_occurrence(client):
    animal_id = _animal(client, "VAX-DUP-01")

    first = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 1",
            "next_due_date": "2026-09-14",
            "schedule_status": "SCHEDULED",
            "operator": "Audit Scheduler",
        },
    )
    assert first.status_code == 200, first.text

    duplicate = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 2",
            "next_due_date": "2026-09-14",
            "schedule_status": "SCHEDULED",
            "operator": "Audit Scheduler",
        },
    )
    assert duplicate.status_code == 409, duplicate.text

    second = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "HS",
            "dose": "Dose 1",
            "next_due_date": "2026-09-15",
            "schedule_status": "SCHEDULED",
            "operator": "Audit Scheduler",
        },
    )
    assert second.status_code == 200, second.text

    amended_duplicate = client.post(
        (
            f"/farm/animals/{animal_id}/vaccinations/"
            f"{second.json()['id']}/amend"
        ),
        json={
            "vaccine": "FMD",
            "dose": "Dose 2",
            "scheduled_date": "2026-09-14",
            "operator": "Audit Amender",
        },
    )
    assert amended_duplicate.status_code == 409, amended_duplicate.text


def test_vaccination_schedule_rejects_empty_amendment_fields(client):
    animal_id = _animal(client, "VAX-AMEND-VALIDATION-01")

    scheduled = client.post(
        f"/farm/animals/{animal_id}/vaccinations",
        json={
            "vaccine": "FMD",
            "dose": "Dose 1",
            "next_due_date": "2026-09-14",
            "schedule_status": "SCHEDULED",
            "operator": "Audit Scheduler",
        },
    )
    assert scheduled.status_code == 200, scheduled.text

    for payload in (
        {
            "vaccine": "",
            "dose": "Dose 2",
            "scheduled_date": "2026-09-15",
        },
        {
            "vaccine": "HS",
            "dose": "",
            "scheduled_date": "2026-09-15",
        },
        {
            "vaccine": "HS",
            "dose": "Dose 2",
            "scheduled_date": "",
        },
    ):
        response = client.post(
            (
                f"/farm/animals/{animal_id}/vaccinations/"
                f"{scheduled.json()['id']}/amend"
            ),
            json=payload,
        )
        assert response.status_code == 422, response.text


def test_vaccination_audit_history_classifies_legacy_event_without_action(
    client,
):
    animal_id = _animal(client, "VAX-AUDIT-LEGACY-01")

    container.input_gateway.record(
        input_type="vaccination",
        payload={
            "animal_id": animal_id,
            "vaccine": "LEGACY-FMD",
            "dose": "1",
            "next_due_date": "2026-09-30",
            "status": "COMPLETED",
        },
        actor="Legacy Audit Test",
    )

    response = client.get(
        "/farm/vaccinations/audit-history",
        params={"animal_id": animal_id},
    )
    assert response.status_code == 200, response.text

    rows = response.json()

    legacy = [
        row
        for row in rows
        if row.get("vaccine") == "LEGACY-FMD"
    ]

    assert len(legacy) == 1
    assert legacy[0]["action"] == "LEGACY"
    assert legacy[0]["scheduled_date"] == "2026-09-30"
    assert legacy[0]["event_id"]

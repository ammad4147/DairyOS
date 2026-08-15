from datetime import datetime, timedelta, timezone
from uuid import uuid4

from dairyos.data.repositories.repository_factory import RepositoryFactory


def _equipment_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def _finding_rows(response):
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict)
    assert isinstance(body.get("findings"), list)
    return body["findings"]


def test_equipment_create_persists_and_reloads(client):
    equipment_id = _equipment_id("EQ-CREATE")

    response = client.post(
        "/farm/equipment",
        json={
            "equipment_id": equipment_id,
            "name": "Main Milking Machine",
            "category": "MILKING",
            "location": "MILKING PARLOR",
            "status": "AVAILABLE",
            "condition": "GOOD",
            "running_hours": 125.0,
            "operator": "Equipment Auditor",
            "activity": "INITIAL_INSPECTION",
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["equipment_id"] == equipment_id
    assert body["name"] == "Main Milking Machine"
    assert body["running_hours"] == 125.0
    assert body["activity"] == "INITIAL_INSPECTION"
    assert body["service_event_id"] is not None

    factory = RepositoryFactory.create()
    try:
        entity = factory.equipment().get_by_equipment_id(
            equipment_id
        )
        assert entity is not None
        assert entity.name == "Main Milking Machine"
        assert entity.status == "AVAILABLE"
        assert entity.condition == "GOOD"
        assert entity.running_hours == 125.0

        history = factory.equipment().service_history(
            equipment_id
        )
        assert len(history) == 1
        assert history[0].id == body["service_event_id"]
    finally:
        factory.close()


def test_equipment_service_history_persists(client):
    equipment_id = _equipment_id("EQ-SERVICE")

    create = client.post(
        "/farm/equipment",
        json={
            "equipment_id": equipment_id,
            "name": "Milk Chiller",
            "category": "COOLING",
            "status": "AVAILABLE",
            "condition": "GOOD",
        },
    )

    assert create.status_code == 200, create.text

    service = client.post(
        f"/farm/equipment/{equipment_id}/service",
        json={
            "event_date": "2026-08-15",
            "event_type": "SCHEDULED_SERVICE",
            "running_hours": 400.0,
            "status_after": "AVAILABLE",
            "next_service_due_at": "2026-09-15T08:00:00+00:00",
            "operator": "Maintenance Lead",
            "notes": "Compressor inspection completed.",
        },
    )

    assert service.status_code == 200, service.text

    service_body = service.json()
    assert service_body["service_event"]["id"] is not None

    history = client.get(
        f"/farm/equipment/{equipment_id}/service-history"
    )

    assert history.status_code == 200, history.text

    rows = history.json()

    assert isinstance(rows, list)

    matching = [
        row
        for row in rows
        if row["id"] == service_body["service_event"]["id"]
    ]

    assert len(matching) == 1

    row = matching[0]

    assert row["equipment_id"] == equipment_id
    assert row["event_type"] == "SCHEDULED_SERVICE"
    assert row["running_hours"] == 400.0
    assert row["event_date"] == "2026-08-15"

    equipment = client.get(
        f"/farm/equipment/{equipment_id}"
    )

    assert equipment.status_code == 200, equipment.text

    body = equipment.json()

    assert body["last_service_at"] is not None
    assert body["next_service_due_at"] is not None
    assert body["next_service_due_at"].startswith(
        "2026-09-15T"
    )


def test_equipment_out_of_service_generates_finding(client):
    equipment_id = _equipment_id("EQ-OOS")

    response = client.post(
        "/farm/equipment",
        json={
            "equipment_id": equipment_id,
            "name": "Backup Generator",
            "category": "POWER",
            "status": "OUT_OF_SERVICE",
            "condition": "POOR",
            "operator": "Equipment Auditor",
            "activity": "FAILURE",
        },
    )

    assert response.status_code == 200, response.text

    rows = _finding_rows(
        client.get(
            "/farm/findings",
            params={"module": "EQUIPMENT"},
        )
    )

    matches = [
        row
        for row in rows
        if row.get("subject_id") == equipment_id
        and row.get("severity") == "HIGH"
    ]

    assert matches


def test_equipment_out_of_service_finding_is_deduplicated(client):
    equipment_id = _equipment_id("EQ-DEDUPE")

    payload = {
        "equipment_id": equipment_id,
        "name": "Feed Mixer",
        "category": "FEED",
        "status": "OUT_OF_SERVICE",
        "condition": "POOR",
        "operator": "Equipment Auditor",
        "activity": "FAILURE",
    }

    first = client.post(
        "/farm/equipment",
        json=payload,
    )
    second = client.post(
        "/farm/equipment",
        json=payload,
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    rows = _finding_rows(
        client.get(
            "/farm/findings",
            params={"module": "EQUIPMENT"},
        )
    )

    matches = [
        row
        for row in rows
        if row.get("subject_id") == equipment_id
        and row.get("severity") == "HIGH"
    ]

    assert len(matches) == 1
    assert matches[0]["observation_count"] >= 2


def test_equipment_overdue_service_generates_finding(client):
    equipment_id = _equipment_id("EQ-OVERDUE")

    response = client.post(
        "/farm/equipment",
        json={
            "equipment_id": equipment_id,
            "name": "Pasteurizer",
            "category": "PROCESSING",
            "status": "AVAILABLE",
            "condition": "FAIR",
            "next_service_due_at": (
                datetime.now(timezone.utc)
                - timedelta(days=3)
            ).isoformat(),
            "operator": "Equipment Auditor",
            "activity": "SERVICE_CHECK",
        },
    )

    assert response.status_code == 200, response.text

    rows = _finding_rows(
        client.get(
            "/farm/findings",
            params={"module": "EQUIPMENT"},
        )
    )

    matches = [
        row
        for row in rows
        if row.get("subject_id") == equipment_id
        and row.get("severity") == "HIGH"
        and "overdue" in str(
            row.get("title", "")
        ).lower()
    ]

    assert matches


def test_equipment_unknown_asset_returns_404(client):
    response = client.get(
        "/farm/equipment/DOES-NOT-EXIST"
    )

    assert response.status_code == 404, response.text


def test_equipment_legacy_operational_status_is_accepted(client):
    equipment_id = _equipment_id("EQ-LEGACY")

    response = client.post(
        "/farm/equipment",
        json={
            "equipment_id": equipment_id,
            "name": "Legacy Status Asset",
            "category": "GENERAL",
            "status": "OPERATIONAL",
            "activity": "INSPECTION",
        },
    )

    assert response.status_code == 200, response.text

    factory = RepositoryFactory.create()
    try:
        entity = factory.equipment().get_by_equipment_id(
            equipment_id
        )
        assert entity is not None
        assert entity.status == "AVAILABLE"
    finally:
        factory.close()


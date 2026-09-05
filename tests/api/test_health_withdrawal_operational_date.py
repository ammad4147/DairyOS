from datetime import datetime, time, timedelta
from uuid import uuid4

from dairyos.api import health as health_api
from dairyos.app import container
from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


def _day():
    return OperationalDateAuthority(
        repository_factory=container.repository_factory
    ).current_date()


def _at_noon(day):
    return datetime.combine(day, time(hour=12))


def _animal(client):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "sex": "FEMALE",
            "lifecycle_status": "LACTATING",
            "ear_tag": f"HL-WD-{uuid4().hex[:10].upper()}",
            "is_currently_milking": True,
            "milking_frequency": "THRICE_DAILY",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def test_expired_withdrawal_is_not_active_in_health_summary(client, monkeypatch):
    today = _day()
    animal_id = _animal(client)

    case = HealthCase(
        case_id=f"HL-WD-{uuid4().hex[:12]}",
        animal_id=animal_id,
        severity="SEVERE",
        diagnosis="Expired withdrawal test",
        status="OPEN",
        opened_at=_at_noon(today - timedelta(days=5)),
        opened_by="Test",
    )
    container.repository_factory.health_cases().add(case)

    container.repository_factory.treatment().add(
        TreatmentRecord(
            animal_id=animal_id,
            diagnosis="Expired withdrawal test",
            medicine="TEST-EXPIRED",
            treated_by="Test",
            treated_at=_at_noon(today - timedelta(days=5)),
            milk_withdrawal_days=2.0,
            milk_withdrawal_until=_at_noon(today - timedelta(days=3)),
            withdrawal_source="manual_override",
            health_case_id=case.id,
        )
    )

    monkeypatch.setattr(
        health_api.OperationalDateAuthority,
        "current_date",
        lambda self: today,
    )

    response = client.get("/farm/health/summary")
    assert response.status_code == 200

    body = response.json()
    assert body["activeClinicalCases"] == 1
    assert body["withdrawalAnimals"] == 0


def test_active_withdrawal_survives_case_resolution(client, monkeypatch):
    today = _day()
    animal_id = _animal(client)

    case = HealthCase(
        case_id=f"HL-WD-{uuid4().hex[:12]}",
        animal_id=animal_id,
        severity="SEVERE",
        diagnosis="Resolved case active withdrawal",
        status="RESOLVED",
        opened_at=_at_noon(today - timedelta(days=2)),
        opened_by="Test",
        resolved_at=_at_noon(today),
        resolved_by="Test",
        resolution="Clinically recovered",
    )
    container.repository_factory.health_cases().add(case)

    container.repository_factory.treatment().add(
        TreatmentRecord(
            animal_id=animal_id,
            diagnosis="Resolved case active withdrawal",
            medicine="TEST-ACTIVE",
            treated_by="Test",
            treated_at=_at_noon(today - timedelta(days=1)),
            milk_withdrawal_days=3.0,
            milk_withdrawal_until=_at_noon(today + timedelta(days=2)),
            withdrawal_source="manual_override",
            health_case_id=case.id,
        )
    )

    monkeypatch.setattr(
        health_api.OperationalDateAuthority,
        "current_date",
        lambda self: today,
    )

    response = client.get("/farm/health/summary")
    assert response.status_code == 200

    body = response.json()
    assert body["activeClinicalCases"] == 0
    assert body["activeSickAnimals"] == 0
    assert body["withdrawalAnimals"] == 1


def test_withdrawal_end_date_is_included_for_day_level_health_projection(
    client,
    monkeypatch,
):
    today = _day()
    animal_id = _animal(client)

    container.repository_factory.treatment().add(
        TreatmentRecord(
            animal_id=animal_id,
            diagnosis="Boundary day test",
            medicine="TEST-BOUNDARY",
            treated_by="Test",
            treated_at=_at_noon(today - timedelta(days=2)),
            milk_withdrawal_days=2.0,
            milk_withdrawal_until=_at_noon(today),
            withdrawal_source="manual_override",
        )
    )

    monkeypatch.setattr(
        health_api.OperationalDateAuthority,
        "current_date",
        lambda self: today,
    )

    response = client.get("/farm/health/summary")
    assert response.status_code == 200
    assert response.json()["withdrawalAnimals"] == 1


def test_future_treatment_is_not_active_yet(client, monkeypatch):
    today = _day()
    animal_id = _animal(client)

    container.repository_factory.treatment().add(
        TreatmentRecord(
            animal_id=animal_id,
            diagnosis="Future treatment test",
            medicine="TEST-FUTURE",
            treated_by="Test",
            treated_at=_at_noon(today + timedelta(days=1)),
            milk_withdrawal_days=3.0,
            milk_withdrawal_until=_at_noon(today + timedelta(days=4)),
            withdrawal_source="manual_override",
        )
    )

    monkeypatch.setattr(
        health_api.OperationalDateAuthority,
        "current_date",
        lambda self: today,
    )

    response = client.get("/farm/health/summary")
    assert response.status_code == 200
    assert response.json()["withdrawalAnimals"] == 0

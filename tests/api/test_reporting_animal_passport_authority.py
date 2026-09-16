from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dairyos.api.reporting_animal_passport import animal_passport_dataset


def _request(*, mode="AS_OF_DATE", selected=date(2026, 8, 31), animal_id="AL-001"):
    return SimpleNamespace(
        filters={"animal_id": animal_id} if animal_id is not None else {},
        period_mode=mode,
        as_of_date=selected if mode == "AS_OF_DATE" else None,
    )


def _passport():
    return {
        "animal": {
            "animal_id": "AL-001",
            "animal_type": "Milking",
            "lifecycle_status": "MILKING",
            "status": "ACTIVE",
            "sex": "FEMALE",
            "breed": "Holstein",
            "date_of_birth": "2022-01-01",
            "dam_id": "DAM-1",
            "sire_id": "SIRE-1",
            "is_currently_milking": True,
            "milking_frequency": 3,
            "production_group": "HIGH",
        },
        "date_context": {
            "mode": "HISTORICAL_STATE",
            "operational_date": "2026-08-31",
        },
        "biological_summary": {
            "lifetime_milk_liters": 12345.6,
            "lactation_count": 3,
            "lifetime_calvings": 3,
            "current_reproductive_status": "CONFIRMED_PREGNANT",
            "current_pregnancy_status": "PREGNANT",
            "days_in_milk": 91,
            "open_health_cases": 1,
            "active_milk_withdrawal": True,
        },
        "schedule": {"milking_frequency": 3, "effective_date": "2026-01-01"},
        "lineage": {"ancestors": [{"animal_id": "DAM-1"}], "descendants": []},
        "record_counts": {"milk": 12, "breeding": 4, "health": 2},
        "timeline": [
            {
                "domain": "milk",
                "timestamp": "2026-08-30",
                "record": {"production_date": "2026-08-30", "total_yield": 31.5},
            }
        ],
    }


def test_reporting_passport_delegates_selected_as_of_date(monkeypatch):
    calls = []

    class Service:
        def __init__(self, factory):
            calls.append(("factory", factory))

        def build(self, animal_id, *, as_of_date):
            calls.append((animal_id, as_of_date))
            return _passport()

    import dairyos.api.reporting_animal_passport as adapter

    monkeypatch.setattr(adapter, "DatabaseAwareLifetimeAnimalPassportService", Service)
    factory = object()
    result = animal_passport_dataset(
        _request(),
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    assert calls == [("factory", factory), ("AL-001", date(2026, 8, 31))]
    assert result["dataset_status"] == "AUTHORITATIVE_PASSPORT_DATASET"
    assert result["summary"]["lifetime_milk_liters"] == 12345.6
    assert result["summary"]["lifetime_calvings"] == 3
    assert result["summary"]["open_health_cases"] == 1
    assert result["summary"]["active_milk_withdrawal"] is True


def test_reporting_passport_current_mode_uses_farm_operational_date(monkeypatch):
    seen = []

    class Service:
        def __init__(self, factory):
            pass

        def build(self, animal_id, *, as_of_date):
            seen.append(as_of_date)
            passport = _passport()
            passport["date_context"] = {
                "mode": "HISTORICAL_STATE",
                "operational_date": as_of_date.isoformat(),
            }
            return passport

    import dairyos.api.reporting_animal_passport as adapter

    monkeypatch.setattr(adapter, "DatabaseAwareLifetimeAnimalPassportService", Service)
    result = animal_passport_dataset(
        _request(mode="CURRENT_HERD"),
        SimpleNamespace(repository_factory=object()),
        date(2026, 9, 16),
    )

    assert seen == [date(2026, 9, 16)]
    assert result["rows"][0]["as_of_date"] == "2026-09-16"


def test_reporting_passport_requires_animal_id():
    with pytest.raises(HTTPException) as exc:
        animal_passport_dataset(
            _request(animal_id=None),
            SimpleNamespace(repository_factory=object()),
            date(2026, 9, 16),
        )
    assert exc.value.status_code == 422


def test_reporting_passport_preserves_canonical_not_found(monkeypatch):
    class Service:
        def __init__(self, factory):
            pass

        def build(self, animal_id, *, as_of_date):
            return None

    import dairyos.api.reporting_animal_passport as adapter

    monkeypatch.setattr(adapter, "DatabaseAwareLifetimeAnimalPassportService", Service)
    with pytest.raises(HTTPException) as exc:
        animal_passport_dataset(
            _request(),
            SimpleNamespace(repository_factory=object()),
            date(2026, 9, 16),
        )
    assert exc.value.status_code == 404


def test_reporting_passport_timeline_is_export_safe_without_recalculation(monkeypatch):
    class Service:
        def __init__(self, factory):
            pass

        def build(self, animal_id, *, as_of_date):
            return _passport()

    import dairyos.api.reporting_animal_passport as adapter

    monkeypatch.setattr(adapter, "DatabaseAwareLifetimeAnimalPassportService", Service)
    result = animal_passport_dataset(
        _request(),
        SimpleNamespace(repository_factory=object()),
        date(2026, 9, 16),
    )

    summary = result["rows"][0]
    event = result["rows"][1]
    assert summary["lifetime_milk_liters"] == 12345.6
    assert summary["current_reproductive_status"] == "CONFIRMED_PREGNANT"
    assert event["row_type"] == "TIMELINE"
    assert event["event_domain"] == "milk"
    assert event["event_timestamp"] == "2026-08-30"
    assert event["event_record"] == "production_date=2026-08-30; total_yield=31.5"
    assert all(not isinstance(value, (dict, list)) for row in result["rows"] for value in row.values())

from datetime import date, datetime
from types import SimpleNamespace

import pytest

import dairyos.milk.services.milk_recording_intelligence_service as intelligence_module
from dairyos.milk.services.milk_recording_intelligence_service import (
    MilkRecordingIntelligenceService,
)


class _Repository:
    def __init__(self, records):
        self._records = list(records)

    def get_all(self):
        return list(self._records)


class _Factory:
    def __init__(self, records):
        self._milk = _Repository(records)

    def milk(self):
        return self._milk


class _TrendServiceStub:
    snapshots = {}

    def __init__(self, repository_factory=None):
        self._repository_factory = repository_factory

    def _get_factory(self):
        return self._repository_factory

    def _eligible_animals(self, factory):
        return [SimpleNamespace(animal_id="M19-001")]

    def _animal_histories(self, factory, animals):
        return {"M19-001": ["animal-history"]}

    def _daily_animal_snapshot(
        self,
        records,
        animal,
        histories,
        target_date,
    ):
        assert histories == ["animal-history"]
        return self.snapshots.get(target_date)


def _record(day: int, total: float):
    return SimpleNamespace(
        animal_id="M19-001",
        production_date=datetime(2026, 8, day),
        total_yield=total,
        morning_yield=None,
        afternoon_yield=None,
        evening_yield=None,
    )


def _repository_service(latest_yield: float):
    return MilkRecordingIntelligenceService(
        _Repository(
            [
                _record(1, 90.0),
                _record(2, 100.0),
                _record(3, 110.0),
                _record(4, latest_yield),
            ]
        )
    )


@pytest.mark.parametrize(
    ("latest_yield", "expected_severity"),
    [
        (85.01, None),
        (85.0, "WARNING"),
        (80.01, "WARNING"),
        (80.0, "CRITICAL"),
    ],
)
def test_m19_compatibility_boundaries(latest_yield, expected_severity):
    alerts = _repository_service(latest_yield).yield_drop_alerts()

    if expected_severity is None:
        assert alerts == []
        return

    assert len(alerts) == 1
    assert alerts[0]["severity"] == expected_severity
    assert alerts[0]["previous_litres"] == 100.0


def test_m19_caller_cannot_lower_warning_threshold_below_15_percent():
    service = _repository_service(85.0)

    alerts = service.yield_drop_alerts(threshold_percent=1.0)

    assert len(alerts) == 1
    assert alerts[0]["drop_percent"] == 15.0
    assert alerts[0]["severity"] == "WARNING"


def test_m19_critical_boundary_is_not_hidden_by_raised_warning_filter():
    service = _repository_service(80.0)

    alerts = service.yield_drop_alerts(threshold_percent=50.0)

    assert len(alerts) == 1
    assert alerts[0]["drop_percent"] == 20.0
    assert alerts[0]["severity"] == "CRITICAL"


def test_m19_authoritative_path_uses_total_litres_and_three_complete_days(
    monkeypatch,
):
    records = [
        _record(10, 999.0),
        _record(11, 999.0),
        _record(12, 999.0),
        _record(13, 999.0),
        _record(14, 999.0),
    ]
    factory = _Factory(records)

    _TrendServiceStub.snapshots = {
        date(2026, 8, 10): {
            "complete": True,
            "total_litres": 90.0,
            "total_yield": 9999.0,
        },
        date(2026, 8, 11): {
            "complete": True,
            "total_litres": 100.0,
            "total_yield": 9999.0,
        },
        date(2026, 8, 12): {
            "complete": False,
            "total_litres": 1.0,
            "total_yield": 9999.0,
        },
        date(2026, 8, 13): {
            "complete": True,
            "total_litres": 110.0,
            "total_yield": 9999.0,
        },
        date(2026, 8, 14): {
            "complete": True,
            "total_litres": 80.0,
            "total_yield": 9999.0,
        },
    }

    monkeypatch.setattr(
        intelligence_module,
        "MilkProductionTrendIntelligenceService",
        _TrendServiceStub,
    )
    monkeypatch.setattr(
        MilkRecordingIntelligenceService,
        "_operational_today",
        lambda self: date(2026, 8, 14),
    )

    service = MilkRecordingIntelligenceService(
        factory.milk(),
        repository_factory=factory,
    )

    alerts = service.yield_drop_alerts()

    assert len(alerts) == 1
    assert alerts[0]["previous_litres"] == 100.0
    assert alerts[0]["latest_litres"] == 80.0
    assert alerts[0]["drop_percent"] == 20.0
    assert alerts[0]["severity"] == "CRITICAL"


def test_m19_api_defaults_to_15_percent_and_floors_lower_callers(client):
    default_response = client.get("/farm/milk/intelligence")
    assert default_response.status_code == 200, default_response.text
    assert default_response.json()["yield_drop_threshold_percent"] == 15.0

    lowered_response = client.get(
        "/farm/milk/intelligence?threshold_percent=1"
    )
    assert lowered_response.status_code == 200, lowered_response.text
    assert lowered_response.json()["yield_drop_threshold_percent"] == 15.0

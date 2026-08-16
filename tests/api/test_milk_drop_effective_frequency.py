from dataclasses import dataclass
from datetime import date

from dairyos.farm.production.services.milk_cycle_monitoring_service import (
    MilkCycleMonitoringService,
)


@dataclass
class FakeHistory:
    milking_frequency: str
    effective_from: object
    effective_to: object = None


@dataclass
class FakeAnimal:
    animal_id: str
    milking_frequency: str


@dataclass
class FakeMilkRow:
    animal_id: str
    production_date: date
    session_ledger: bool
    status: str
    morning_yield: float | None
    afternoon_yield: float | None
    evening_yield: float | None
    total_yield: float | None


class FakeAnimalRepository:
    def __init__(self, animal, history):
        self.animal = animal
        self.history = history

    def get_by_animal_id(self, animal_id):
        if animal_id == self.animal.animal_id:
            return self.animal
        return None

    def get_milking_frequency_history(self, animal_id):
        if animal_id == self.animal.animal_id:
            return list(self.history)
        return []


class FakeMilkRepository:
    def __init__(self, rows):
        self.rows = rows

    def get_by_animal_id(self, animal_id):
        return [
            row
            for row in self.rows
            if row.animal_id == animal_id
        ]


class FakeFindingsRepository:
    pass


class FakeFactory:
    def __init__(self, animal, history, rows):
        self.animal_repo = FakeAnimalRepository(
            animal,
            history,
        )
        self.milk_repo = FakeMilkRepository(rows)
        self.findings_repo = FakeFindingsRepository()

    def animal(self):
        return self.animal_repo

    def milk(self):
        return self.milk_repo

    def operational_findings(self):
        return self.findings_repo

    def close(self):
        return None


def test_monitoring_uses_frequency_effective_on_current_operational_date(
    monkeypatch,
):
    animal = FakeAnimal(
        animal_id="TEST-MILK-FREQ-001",
        milking_frequency="TWICE_DAILY",
    )

    history = [
        FakeHistory(
            milking_frequency="THRICE_DAILY",
            effective_from="2026-08-15T00:00:00",
            effective_to="2026-08-16T00:00:00",
        ),
        FakeHistory(
            milking_frequency="TWICE_DAILY",
            effective_from="2026-08-16T00:00:00",
        ),
    ]

    rows = [
        FakeMilkRow(
            animal_id=animal.animal_id,
            production_date=date(2026, 8, 15),
            session_ledger=True,
            status="RECORDED",
            morning_yield=10.0,
            afternoon_yield=9.0,
            evening_yield=8.0,
            total_yield=27.0,
        )
    ]

    factory = FakeFactory(
        animal,
        history,
        rows,
    )

    captured = {}

    def fake_detect_drop(*args, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_cycle_monitoring_service.detect_drop",
        fake_detect_drop,
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_cycle_monitoring_service.MilkCycleMonitoringService._finding",
        staticmethod(lambda *args, **kwargs: None),
    )

    result = MilkCycleMonitoringService(
        repository_factory=factory,
    ).monitor(
        animal_id=animal.animal_id,
        milking_session="AFTERNOON",
        production_date=date(2026, 8, 15),
    )

    assert result["frequency"] == "THRICE_DAILY"
    assert result["status"] != "UNSCHEDULED_SESSION"

    schedule_service = captured["schedule_service"]
    assert schedule_service.get_frequency_for_date(
        animal,
        date(2026, 8, 15),
    ) == "THRICE_DAILY"


def test_monitoring_passes_date_aware_schedule_to_individual_drop_detector(
    monkeypatch,
):
    animal = FakeAnimal(
        animal_id="TEST-MILK-FREQ-002",
        milking_frequency="THRICE_DAILY",
    )

    history = [
        FakeHistory(
            milking_frequency="TWICE_DAILY",
            effective_from="2026-08-15T00:00:00",
            effective_to="2026-08-17T00:00:00",
        ),
        FakeHistory(
            milking_frequency="THRICE_DAILY",
            effective_from="2026-08-17T00:00:00",
        ),
    ]

    rows = [
        FakeMilkRow(
            animal_id=animal.animal_id,
            production_date=date(2026, 8, 16),
            session_ledger=True,
            status="RECORDED",
            morning_yield=10.0,
            afternoon_yield=None,
            evening_yield=10.0,
            total_yield=20.0,
        ),
        FakeMilkRow(
            animal_id=animal.animal_id,
            production_date=date(2026, 8, 17),
            session_ledger=True,
            status="RECORDED",
            morning_yield=4.0,
            afternoon_yield=None,
            evening_yield=4.0,
            total_yield=8.0,
        ),
    ]

    factory = FakeFactory(
        animal,
        history,
        rows,
    )

    captured = {}

    def fake_detect_drop(*args, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_cycle_monitoring_service.detect_drop",
        fake_detect_drop,
    )

    monkeypatch.setattr(
        "dairyos.farm.production.services.milk_cycle_monitoring_service.MilkCycleMonitoringService._finding",
        staticmethod(lambda *args, **kwargs: None),
    )

    result = MilkCycleMonitoringService(
        repository_factory=factory,
    ).monitor(
        animal_id=animal.animal_id,
        milking_session="EVENING",
        production_date=date(2026, 8, 17),
    )

    assert result["frequency"] == "THRICE_DAILY"
    assert result["status"] == "NO_COMPARISON"
    assert captured["animal"] is animal
    assert captured["as_of_date"] == date(2026, 8, 17)
    assert captured["schedule_service"].get_frequency_for_date(
        animal,
        date(2026, 8, 16),
    ) == "TWICE_DAILY"
    assert captured["schedule_service"].get_frequency_for_date(
        animal,
        date(2026, 8, 17),
    ) == "THRICE_DAILY"


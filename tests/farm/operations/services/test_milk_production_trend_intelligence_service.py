from datetime import date
from types import SimpleNamespace

from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)


DAY = date(2026, 8, 15)


def animal(animal_id="A1", frequency="TWICE_DAILY"):
    return SimpleNamespace(
        animal_id=animal_id,
        milking_frequency=frequency,
        is_currently_milking=True,
        active=True,
    )


def history(frequency, effective_from, effective_to=None):
    return SimpleNamespace(
        milking_frequency=frequency,
        effective_from=effective_from,
        effective_to=effective_to,
    )


def row(
    animal_id,
    day,
    session,
    *,
    morning=None,
    afternoon=None,
    evening=None,
    total=None,
    session_ledger=True,
    status="RECORDED",
):
    return SimpleNamespace(
        animal_id=animal_id,
        production_date=day,
        milking_session=session,
        morning_yield=morning,
        afternoon_yield=afternoon,
        evening_yield=evening,
        total_yield=total,
        session_ledger=session_ledger,
        status=status,
    )


class FakeAnimalRepo:
    def __init__(self, animals, histories):
        self._animals = animals
        self._histories = histories

    def get_all(self):
        return self._animals

    def get_milking_frequency_history(self, animal_id):
        return self._histories.get(animal_id, [])


class FakeMilkRepo:
    def __init__(self, records):
        self._records = records

    def get_all(self):
        return self._records


class FakeFactory:
    def __init__(self, animals, records, histories=None):
        self.session = object()
        self._animals = animals
        self._records = records
        self._histories = histories or {}

    def animal(self):
        return FakeAnimalRepo(self._animals, self._histories)

    def milk(self):
        return FakeMilkRepo(self._records)

    def close(self):
        pass


def test_incomplete_current_day_is_not_reported_as_complete():
    records = [
        row("A1", DAY, "MORNING", morning=10.0),
    ]
    service = MilkProductionTrendIntelligenceService(
        FakeFactory([animal()], records)
    )

    result = service.generate(
        as_of_date=DAY,
        period_days=7,
    )

    assert result["complete"] is False
    assert result["daily_total"] is None
    assert result["comparison_status"] == "NO_COMPARISON"


def test_complete_current_and_prior_days_are_compared_by_daily_total():
    records = [
        row("A1", DAY, "MORNING", morning=7.0),
        row("A1", DAY, "EVENING", evening=8.0),
        row("A1", DAY.replace(day=14), "MORNING", morning=10.0),
        row("A1", DAY.replace(day=14), "EVENING", evening=10.0),
    ]
    service = MilkProductionTrendIntelligenceService(
        FakeFactory([animal()], records)
    )

    result = service.generate(
        as_of_date=DAY,
        period_days=7,
    )

    assert result["complete"] is True
    assert result["daily_total"] == 15.0
    assert result["prior_total_litres"] == 20.0
    assert result["variance_litres"] == -5.0
    assert result["variance_percentage"] == -25.0
    assert result["comparison_status"] == "COMPARED"


def test_incomplete_calendar_day_is_skipped_when_finding_prior_comparable_day():
    records = [
        row("A1", DAY, "MORNING", morning=7.0),
        row("A1", DAY, "EVENING", evening=8.0),
        row("A1", DAY.replace(day=14), "MORNING", morning=10.0),
        # Evening deliberately missing on the 14th.
        row("A1", DAY.replace(day=13), "MORNING", morning=9.0),
        row("A1", DAY.replace(day=13), "EVENING", evening=9.0),
    ]
    service = MilkProductionTrendIntelligenceService(
        FakeFactory([animal()], records)
    )

    result = service.generate(
        as_of_date=DAY,
        period_days=7,
    )

    assert result["prior_date"] == "2026-08-13"
    assert result["prior_total_litres"] == 18.0
    assert result["comparison_status"] == "COMPARED"


def test_session_ledger_false_is_excluded():
    records = [
        row(
            "A1",
            DAY.replace(day=14),
            "MORNING",
            morning=10.0,
            session_ledger=False,
        ),
        row(
            "A1",
            DAY.replace(day=14),
            "EVENING",
            evening=10.0,
            session_ledger=False,
        ),
        row("A1", DAY, "MORNING", morning=7.0),
        row("A1", DAY, "EVENING", evening=8.0),
    ]
    service = MilkProductionTrendIntelligenceService(
        FakeFactory([animal()], records)
    )

    result = service.generate(
        as_of_date=DAY,
        period_days=7,
    )

    assert result["comparison_status"] == "NO_COMPARISON"


def test_frequency_history_controls_expected_sessions_for_date():
    records = [
        row("A1", DAY, "MORNING", morning=6.0),
        row("A1", DAY, "AFTERNOON", afternoon=5.0),
        row("A1", DAY, "EVENING", evening=4.0),
    ]
    histories = {
        "A1": [
            history(
                "THRICE_DAILY",
                effective_from=DAY,
            )
        ]
    }

    service = MilkProductionTrendIntelligenceService(
        FakeFactory(
            [animal(frequency="TWICE_DAILY")],
            records,
            histories,
        )
    )

    result = service.generate(
        as_of_date=DAY,
        period_days=7,
    )

    assert result["complete"] is True
    assert result["daily_total"] == 15.0


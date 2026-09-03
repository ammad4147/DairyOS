from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

from dairyos.farm.production.services.missed_milking_control_service import (
    MissedMilkingControlService,
)


class _AnimalRepo:
    def __init__(self, animal):
        self._animal = animal

    def get_all(self):
        return [self._animal]

    def get_milking_frequency_history(self, animal_id):
        return []


class _MilkRepo:
    def __init__(self, rows):
        self._rows = rows

    def get_all(self):
        return list(self._rows)


class _SessionLedger:
    def __init__(self, rows=None):
        self._rows = list(rows or [])

    def earliest_date(self):
        return date(2026, 9, 3)

    def get_by_date(self, production_date):
        return [
            row
            for row in self._rows
            if row.operational_date == production_date
        ]


class _FindingRepo:
    def get_all(self):
        return []


class _Factory:
    def __init__(self, animal, milk_rows, session_rows=None):
        self._animal = _AnimalRepo(animal)
        self._milk = _MilkRepo(milk_rows)
        self._ledger = _SessionLedger(session_rows)
        self._findings = _FindingRepo()

    def animal(self):
        return self._animal

    def milk(self):
        return self._milk

    def milking_session_ledger(self):
        return self._ledger

    def operational_findings(self):
        return self._findings


def _animal():
    return SimpleNamespace(
        animal_id="TD-001",
        active=True,
        is_currently_milking=True,
        lifecycle_status="LACTATING",
        milking_frequency="THRICE_DAILY",
        non_milking_directive="NONE",
        created_at=datetime(2026, 9, 3, 8, 0, 0),
        updated_at=datetime(2026, 9, 3, 8, 0, 0),
        date_of_acquisition=None,
    )


def _partial_row():
    return SimpleNamespace(
        animal_id="TD-001",
        production_date=datetime(2026, 9, 3, 0, 0, 0),
        recorded_at=datetime(2026, 9, 3, 18, 0, 0),
        session_ledger=True,
        status="RECORDED",
        milking_session="AFTERNOON",
        morning_yield=10.0,
        afternoon_yield=9.0,
        evening_yield=None,
        total_yield=19.0,
    )


def test_completed_day_missing_evening_is_actionable():
    service = MissedMilkingControlService(
        _Factory(_animal(), [_partial_row()])
    )
    result = service.inspect(
        as_of_date=date(2026, 9, 4),
        lookback_days=7,
    )

    assert result["active_count"] == 1
    item = result["active"][0]
    assert item["production_date"] == "2026-09-03"
    assert item["animal_id"] == "TD-001"
    assert item["recorded_sessions"] == ["MORNING", "AFTERNOON"]
    assert item["missing_sessions"] == ["EVENING"]


def test_whole_farm_not_milked_session_settles_occurrence():
    farm_skip = SimpleNamespace(
        operational_date=date(2026, 9, 3),
        milking_session="EVENING",
        status="NOT_MILKED",
    )
    service = MissedMilkingControlService(
        _Factory(
            _animal(),
            [_partial_row()],
            [farm_skip],
        )
    )
    result = service.inspect(
        as_of_date=date(2026, 9, 4),
        lookback_days=7,
    )

    assert result["active_count"] == 0


def test_ui_and_api_contracts_are_present():
    root = Path(__file__).resolve().parents[2]
    milk = (
        root
        / "src"
        / "DairyOS.Web"
        / "src"
        / "components"
        / "MilkTab.tsx"
    ).read_text(encoding="utf-8")
    animals = (
        root
        / "src"
        / "DairyOS.Web"
        / "src"
        / "components"
        / "AnimalTab.tsx"
    ).read_text(encoding="utf-8")
    finance = (
        root
        / "src"
        / "DairyOS.Web"
        / "src"
        / "components"
        / "FinanceTab.tsx"
    ).read_text(encoding="utf-8")
    alerts = (
        root
        / "src"
        / "DairyOS.Web"
        / "src"
        / "context"
        / "AlertAuditContext.tsx"
    ).read_text(encoding="utf-8")
    api = (
        root
        / "src"
        / "dairyos"
        / "api"
        / "milk_traceability.py"
    ).read_text(encoding="utf-8")

    assert "Milk Quality Log" in milk
    assert "Save CSV" in milk
    assert "Print" in milk
    assert "Missed Milking — Action Required" in milk
    assert "MISSED_MILK_REJECTED:" in milk
    assert "Closing Milk Balance" in milk
    assert "Opening Milk Balance" in milk
    compact_animals = "".join(animals.split())
    assert "numeric:true" in compact_animals
    assert "onAnimalChanged" in finance
    assert "60 * 1000" in alerts
    assert "/missed-sessions/reconcile" in api

    # M-19: only genuine individual-animal daily yield declines may enter
    # the Dashboard Yield Drop Watchlist. Farm-level MILK reconciliation
    # findings and other MILK operational controls must not be classified
    # as MILK_DROP merely because their source_module is MILK.
    assert "function mapSource(finding: FindingPayload)" in alerts
    assert "MILK_DAILY_DROP:" in alerts
    assert "title.includes('milk yield declined')" in alerts
    assert "subjectType === 'FARM'" in alerts
    assert "return 'RECONCILIATION';" in alerts
    assert "source: mapSource(finding)" in alerts
    assert "case 'MILK': return 'MILK_DROP';" not in alerts

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from dairyos.api import reporting_milk


class Repo:
    def __init__(self, records=None):
        self.records = list(records or [])

    def get_all(self):
        return list(self.records)

    def get_by_date(self, selected):
        return [
            row for row in self.records
            if reporting_milk._plain_date(getattr(row, "production_date", None)) == selected
        ]


class CorrectionRepo:
    def __init__(self, by_id=None):
        self.by_id = dict(by_id or {})

    def get_for_production(self, production_id):
        return list(self.by_id.get(production_id, []))


class AnimalRepo:
    def __init__(self, animals):
        self.animals = {animal.animal_id: animal for animal in animals}

    def get_by_animal_id(self, animal_id):
        return self.animals.get(str(animal_id))

    def get_milking_frequency_history(self, animal_id):
        return []


class Factory:
    def __init__(self, *, milk, corrections=None, dispositions=None, animals=None):
        self._milk = milk
        self._corrections = corrections or CorrectionRepo()
        self._dispositions = dispositions or Repo()
        self._animals = AnimalRepo(animals or [])

    def milk(self):
        return self._milk

    def milk_corrections(self):
        return self._corrections

    def milk_dispositions(self):
        return self._dispositions

    def animal(self):
        return self._animals


class FactoryWithoutCorrections:
    def __init__(self, *, milk, animals=None):
        self._milk = milk
        self._animals = AnimalRepo(animals or [])

    def milk(self):
        return self._milk

    def animal(self):
        return self._animals


def request(report_id, period_mode, **kwargs):
    filters = kwargs.pop("filters", {})
    return SimpleNamespace(
        report_id=report_id,
        period_mode=period_mode,
        filters=filters,
        operational_date=kwargs.pop("operational_date", None),
        start_date=kwargs.pop("start_date", None),
        end_date=kwargs.pop("end_date", None),
        as_of_date=kwargs.pop("as_of_date", None),
    )


def production(**overrides):
    values = dict(
        id=1,
        animal_id="A-001",
        production_date=datetime(2026, 9, 15, 8, 0),
        recorded_at=datetime(2026, 9, 15, 8, 5),
        milking_session="EVENING",
        session_ledger=True,
        morning_yield=10.0,
        afternoon_yield=8.0,
        evening_yield=9.0,
        total_yield=27.0,
        status="RECORDED",
        notes=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def animal(animal_id="A-001", frequency="THRICE_DAILY"):
    return SimpleNamespace(
        animal_id=animal_id,
        milking_frequency=frequency,
        non_milking_directive="NONE",
    )


def test_empty_production_without_correction_repository_remains_authoritative():
    factory = FactoryWithoutCorrections(milk=Repo([]))
    payload = request(
        "daily-milk",
        "OPERATIONAL_DATE",
        operational_date=date(2026, 9, 15),
    )

    result = reporting_milk.milk_reporting_dataset(
        payload,
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    assert result["dataset_status"] == "AUTHORITATIVE_MILK_PRODUCTION_DATASET"
    assert result["rows"] == []
    assert result["summary"]["active_milk_litres"] == 0.0
    assert result["summary"]["correction_records"] == 0


def test_nonempty_production_without_correction_repository_fails_closed():
    factory = FactoryWithoutCorrections(milk=Repo([production()]), animals=[animal()])
    payload = request(
        "daily-milk",
        "OPERATIONAL_DATE",
        operational_date=date(2026, 9, 15),
    )

    with pytest.raises(HTTPException) as exc:
        reporting_milk.milk_reporting_dataset(
            payload,
            SimpleNamespace(repository_factory=factory),
            date(2026, 9, 16),
        )

    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "REPORTING_AUTHORITY_UNAVAILABLE"
    assert exc.value.detail["authority"] == "MilkCorrections"


def test_daily_milk_preserves_three_sessions_and_excludes_void_from_active_total():
    active = production()
    void = production(id=2, total_yield=300.0, morning_yield=100.0, afternoon_yield=100.0, evening_yield=100.0, status="VOID")
    legacy = production(id=3, total_yield=50.0, session_ledger=False)
    factory = Factory(milk=Repo([active, void, legacy]), animals=[animal()])
    payload = request(
        "daily-milk",
        "OPERATIONAL_DATE",
        operational_date=date(2026, 9, 15),
    )

    result = reporting_milk.milk_reporting_dataset(
        payload,
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    production_rows = [row for row in result["rows"] if row["row_type"] == "PRODUCTION"]
    assert production_rows[0]["morning_yield"] == 10.0
    assert production_rows[0]["afternoon_yield"] == 8.0
    assert production_rows[0]["evening_yield"] == 9.0
    assert result["summary"]["active_milk_litres"] == 27.0
    assert result["summary"]["void_excluded_from_active_totals"] is True


def test_session_view_is_distinct_and_uses_only_selected_session_for_total():
    factory = Factory(milk=Repo([production()]), animals=[animal()])
    payload = request(
        "daily-milk",
        "OPERATIONAL_DATE",
        operational_date=date(2026, 9, 15),
        filters={"session": "AFTERNOON"},
    )

    result = reporting_milk.milk_reporting_dataset(
        payload,
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    row = result["rows"][0]
    assert row["session"] == "AFTERNOON"
    assert row["session_yield_litres"] == 8.0
    assert "morning_yield" not in row
    assert "evening_yield" not in row
    assert result["summary"]["active_milk_litres"] == 8.0


def test_milk_animal_filters_identity_and_effective_milking_cohort():
    second = production(id=2, animal_id="A-002", total_yield=20.0)
    factory = Factory(
        milk=Repo([production(), second]),
        animals=[animal(), animal("A-002", "TWICE_DAILY")],
    )
    payload = request(
        "milk-animal",
        "DATE_RANGE",
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 15),
        filters={"animal_id": "A-002", "milking_cohort": "TWICE_DAILY"},
    )

    result = reporting_milk.milk_reporting_dataset(
        payload,
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    production_rows = [row for row in result["rows"] if row["row_type"] == "PRODUCTION"]
    assert [row["animal_id"] for row in production_rows] == ["A-002"]
    assert production_rows[0]["milking_cohort"] == "TWICE_DAILY"


def test_corrections_are_retained_as_audit_rows_without_recalculating_current_total():
    correction = SimpleNamespace(
        id=91,
        production_id=1,
        action="CORRECT",
        reason="meter correction",
        operator="tester",
        before_json={"total_yield": 25.0},
        after_json={"total_yield": 27.0},
        corrected_at=datetime(2026, 9, 15, 12, 0),
    )
    factory = Factory(
        milk=Repo([production()]),
        corrections=CorrectionRepo({1: [correction]}),
        animals=[animal()],
    )
    payload = request(
        "daily-milk",
        "OPERATIONAL_DATE",
        operational_date=date(2026, 9, 15),
    )

    result = reporting_milk.milk_reporting_dataset(
        payload,
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    assert result["summary"]["active_milk_litres"] == 27.0
    assert result["summary"]["correction_records"] == 1
    assert any(row["row_type"] == "CORRECTION" and row["action"] == "CORRECT" for row in result["rows"])


def test_historical_period_uses_production_operational_date_not_recorded_at():
    row = production(
        production_date=datetime(2026, 9, 10, 23, 30),
        recorded_at=datetime(2026, 9, 16, 1, 0),
    )
    factory = Factory(milk=Repo([row]), animals=[animal()])
    payload = request(
        "daily-milk",
        "OPERATIONAL_DATE",
        operational_date=date(2026, 9, 10),
    )

    result = reporting_milk.milk_reporting_dataset(
        payload,
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    assert result["summary"]["active_milk_litres"] == 27.0
    assert result["rows"][0]["operational_date"] == "2026-09-10"


def test_non_authoritative_historical_category_filter_fails_closed():
    factory = Factory(milk=Repo([production()]), animals=[animal()])
    payload = request(
        "daily-milk",
        "OPERATIONAL_DATE",
        operational_date=date(2026, 9, 15),
        filters={"category": "Milking"},
    )

    with pytest.raises(HTTPException) as exc:
        reporting_milk.milk_reporting_dataset(
            payload,
            SimpleNamespace(repository_factory=factory),
            date(2026, 9, 16),
        )
    assert exc.value.status_code == 422
    assert "effective-dated category authority" in str(exc.value.detail)


def test_disposition_report_consumes_reconciliation_authority_and_retains_void_rows(monkeypatch):
    dispositions = Repo([
        SimpleNamespace(
            id=1,
            production_date=date(2026, 9, 15),
            disposition_type="SOLD",
            quantity_litres=20.0,
            status="RECORDED",
            sale_id="SALE-1",
            amount_due=2000.0,
            amount_received=1500.0,
        ),
        SimpleNamespace(
            id=2,
            production_date=date(2026, 9, 15),
            disposition_type="WASTAGE",
            quantity_litres=7.0,
            status="VOID",
            sale_id=None,
            amount_due=0.0,
            amount_received=0.0,
        ),
    ])
    factory = Factory(milk=Repo([production()]), dispositions=dispositions, animals=[animal()])
    calls = []

    class FakeReconciliation:
        def __init__(self, *, disposition_repository, production_repository):
            assert disposition_repository is dispositions
            assert production_repository is factory._milk

        def reconcile(self, selected, *, raise_finding=True):
            calls.append((selected, raise_finding))
            return {
                "status": "UNACCOUNTED_PRODUCTION",
                "production_complete": True,
                "produced_litres": 27.0,
                "saleable_litres": 27.0,
                "withdrawal_litres": 0.0,
                "accounted_litres": 20.0,
                "sold_litres": 20.0,
                "non_sale_accounted_litres": 0.0,
                "unaccounted_litres": 7.0,
                "over_accounted_litres": 0.0,
                "sale_value": 2000.0,
                "cash_received": 1500.0,
                "receivable_outstanding": 500.0,
            }

    monkeypatch.setattr(reporting_milk, "MilkReconciliationService", FakeReconciliation)
    payload = request(
        "milk-disposition",
        "DATE_RANGE",
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 15),
    )

    result = reporting_milk.milk_reporting_dataset(
        payload,
        SimpleNamespace(repository_factory=factory),
        date(2026, 9, 16),
    )

    assert calls == [(date(2026, 9, 15), False)]
    assert result["summary"]["produced_litres"] == 27.0
    assert result["summary"]["accounted_litres"] == 20.0
    assert result["summary"]["unaccounted_litres"] == 7.0
    assert result["summary"]["void_excluded_by_reconciliation_authority"] is True
    assert any(row["row_type"] == "DISPOSITION" and row["status"] == "VOID" for row in result["rows"])
    assert any(row["row_type"] == "RECONCILIATION" and row["reconciliation_status"] == "UNACCOUNTED_PRODUCTION" for row in result["rows"])

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from dairyos.api.authorization import permission_for_request
from dairyos.api.reporting import (
    ANIMAL_CATEGORY_ORDER,
    REPORTS,
    ReportingRequest,
    _resolved_period,
    reporting_permission_for_request,
    reporting_preview,
)


EXPECTED_REPORT_IDS = {
    "animal-register", "animal-population", "animal-lifecycle", "animal-passport",
    "daily-milk", "milk-animal", "milk-disposition", "milk-quality-log", "quality-summary",
    "current-tmr", "historical-tmr", "finance-ledger", "financial-summary",
    "breeding-cycle", "breeding-performance", "health-cases", "withdrawal",
    "vaccination-schedule", "coml-period", "whole-farm-snapshot",
}


def test_reporting_catalog_has_expected_unique_reports():
    ids = [report.id for report in REPORTS]
    assert len(ids) == len(set(ids))
    assert set(ids) == EXPECTED_REPORT_IDS


def test_reporting_catalog_is_read_only_by_contract():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8-sig")
    assert '@router.get("/catalog")' in source
    assert '@router.post("/preview")' in source
    assert "@router.put(" not in source
    assert "@router.patch(" not in source
    assert "@router.delete(" not in source
    assert ".commit(" not in source
    assert ".add(" not in source
    assert ".delete(" not in source


def test_reporting_uses_operational_date_authority():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8-sig")
    assert "OperationalDateAuthority" in source
    assert "date.today(" not in source
    assert "datetime.now(" not in source
    assert "datetime.utcnow(" not in source
    assert "utcnow(" not in source


def test_unknown_report_is_rejected():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="not-a-report", domain="ANIMALS", period_mode="CURRENT_HERD")


def test_report_domain_mismatch_is_rejected():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="daily-milk", domain="FINANCE", period_mode="TODAY")


def test_unsupported_period_mode_is_rejected():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="daily-milk", domain="MILK", period_mode="CURRENT_YEAR")


def test_range_requires_both_dates():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="finance-ledger", domain="FINANCE", period_mode="DATE_RANGE", start_date=date(2026, 9, 1))


def test_reverse_range_is_rejected():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="finance-ledger", domain="FINANCE", period_mode="DATE_RANGE", start_date=date(2026, 9, 15), end_date=date(2026, 9, 1))


def test_unknown_filter_is_rejected():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="daily-milk", domain="MILK", period_mode="TODAY", filters={"not_a_real_filter": "x"})


def test_valid_daily_milk_request():
    request = ReportingRequest(report_id="daily-milk", domain="MILK", period_mode="TODAY", filters={"session": "MORNING", "milking_cohort": "3x"})
    assert request.report_id == "daily-milk"


def test_today_uses_farm_operational_date():
    request = ReportingRequest(report_id="daily-milk", domain="MILK", period_mode="TODAY")
    period = _resolved_period(request, operational_today=date(2026, 9, 15))
    assert period == {"start_date": "2026-09-15", "end_date": "2026-09-15", "as_of_date": "2026-09-15"}


def test_yesterday_uses_farm_operational_date():
    request = ReportingRequest(report_id="daily-milk", domain="MILK", period_mode="YESTERDAY")
    period = _resolved_period(request, operational_today=date(2026, 9, 15))
    assert period == {"start_date": "2026-09-14", "end_date": "2026-09-14", "as_of_date": "2026-09-14"}


def test_snapshot_date_is_explicit():
    request = ReportingRequest(report_id="whole-farm-snapshot", domain="WHOLE_FARM", period_mode="SNAPSHOT_DATE", snapshot_date=date(2026, 9, 14))
    period = _resolved_period(request, operational_today=date(2026, 9, 15))
    assert period["as_of_date"] == "2026-09-14"
    assert period["end_date"] == "2026-09-14"


def test_single_domain_permission_mapping():
    assert reporting_permission_for_request("finance-ledger") == "finance.view"
    assert reporting_permission_for_request("daily-milk") == "milk.view"
    assert reporting_permission_for_request("health-cases") == "health.view"


def test_semen_stock_is_not_a_reporting_contract():
    assert all(report.id != "semen-stock" for report in REPORTS)
    assert reporting_permission_for_request("semen-stock") == "settings.view"
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="semen-stock", domain="BREEDING", period_mode="AS_OF_DATE", as_of_date=date(2026, 9, 15))


def test_whole_farm_requires_all_governed_domain_permissions():
    definition = next(report for report in REPORTS if report.id == "whole-farm-snapshot")
    assert set(definition.required_permissions) == {"animals.view", "milk.view", "feed.view", "finance.view", "breeding.view", "health.view", "coml.view", "analytics.view"}


def test_authorization_routes_reporting_catalog_to_settings_view():
    assert permission_for_request("GET", "/farm/reporting/catalog") == "settings.view"


def test_authorization_routes_finance_preview_to_finance_view():
    assert permission_for_request("POST", "/farm/reporting/preview", {"report_id": "finance-ledger"}) == "finance.view"


def test_reporting_router_is_registered_once():
    source = Path("src/dairyos/app.py").read_text(encoding="utf-8-sig")
    assert source.count("from dairyos.api.reporting import router as reporting_router") == 1
    assert source.count("app.include_router(reporting_router)") == 1


def test_preview_foundation_keeps_fail_closed_contract_available():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8-sig")
    assert '"DATASET_NOT_IMPLEMENTED"' in source
    assert "No farm values have been" in source
    assert "fabricated." in source


def test_no_exporter_is_introduced_in_foundation():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8-sig").lower()
    assert "reportlab" not in source
    assert "openpyxl" not in source
    assert "xlsxwriter" not in source
    assert "weasyprint" not in source


def test_animal_current_reports_do_not_advertise_historical_state():
    definitions = {report.id: report for report in REPORTS if report.id in {"animal-register", "animal-population"}}
    for definition in definitions.values():
        assert definition.period_modes == ("CURRENT_HERD",)
        assert definition.historical_capability == "CURRENT_ONLY"


def test_animal_register_as_of_date_fails_closed():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="AS_OF_DATE", as_of_date=date(2026, 9, 1))


def test_animal_population_as_of_date_fails_closed():
    with pytest.raises(ValidationError):
        ReportingRequest(report_id="animal-population", domain="ANIMALS", period_mode="AS_OF_DATE", as_of_date=date(2026, 9, 1))


class _FakeAnimalRepository:
    def __init__(self, animals):
        self.animals = list(animals)
        self.get_all_calls = 0

    def get_all(self):
        self.get_all_calls += 1
        return list(self.animals)


class _FakeEmptyMilkRepository:
    def get_all(self):
        return []


class _FoundationRepositoryFactory:
    def milk(self):
        return _FakeEmptyMilkRepository()


def _animal(animal_id, lifecycle_status, sex, *, status="ACTIVE", active=True, is_currently_milking=False, milking_frequency=None):
    return SimpleNamespace(id=None, animal_id=animal_id, legacy_animal_id=None, ear_tag=f"EAR-{animal_id}", rfid=None, breed="TEST", sex=sex, date_of_birth=date(2024, 1, 1), date_of_acquisition=None, dam_id=None, sire_id=None, lifecycle_status=lifecycle_status, status=status, is_currently_milking=is_currently_milking, milking_frequency=milking_frequency, active=active)


def _all_category_animals():
    return [
        _animal("MILK-001", "LACTATING", "FEMALE", is_currently_milking=True, milking_frequency="THRICE"),
        _animal("DRY-001", "DRY", "FEMALE"), _animal("HEIFER-001", "HEIFER", "FEMALE"),
        _animal("FC-001", "CALF", "FEMALE"), _animal("MC-001", "CALF", "MALE"), _animal("BULL-001", "BULL", "MALE"),
    ]


def _container(animals):
    repository = _FakeAnimalRepository(animals)
    return SimpleNamespace(animal_repository=repository, repository_factory=_FoundationRepositoryFactory()), repository


class _FixedOperationalDateAuthority:
    def current_date(self):
        return date(2026, 9, 15)

    def current_datetime(self):
        return datetime(2026, 9, 15, 12, 30, tzinfo=timezone(timedelta(hours=5)))


def test_animal_register_uses_all_six_canonical_categories(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, repository = _container(_all_category_animals())
    result = reporting_preview(ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD"), container=container)
    assert repository.get_all_calls == 1
    assert result["dataset_status"] == "AUTHORITATIVE_CURRENT_DATASET"
    assert result["authority_status"] == "AUTHORITY_AVAILABLE"
    assert result["read_only"] is True
    assert result["record_count"] == 6
    assert {row["category"] for row in result["rows"]} == set(ANIMAL_CATEGORY_ORDER)
    assert result["summary"]["category_counts"] == {"Milking": 1, "Dry": 1, "Heifer": 1, "Female Calf": 1, "Male Calf": 1, "Bull": 1}
    assert result["summary"]["herd_totals"] == {"Milking Cows": 1, "Dry Cows": 1, "Heifers": 1, "Female Calves": 1, "Male Calves": 1, "Bulls": 1}


def test_animal_population_uses_plural_herd_labels(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, _ = _container(_all_category_animals())
    result = reporting_preview(ReportingRequest(report_id="animal-population", domain="ANIMALS", period_mode="CURRENT_HERD"), container=container)
    assert result["rows"] == [
        {"category": "Milking", "herd_total_label": "Milking Cows", "count": 1}, {"category": "Dry", "herd_total_label": "Dry Cows", "count": 1},
        {"category": "Heifer", "herd_total_label": "Heifers", "count": 1}, {"category": "Female Calf", "herd_total_label": "Female Calves", "count": 1},
        {"category": "Male Calf", "herd_total_label": "Male Calves", "count": 1}, {"category": "Bull", "herd_total_label": "Bulls", "count": 1},
    ]


@pytest.mark.parametrize("terminal_status", ["SOLD", "CULLED", "DECEASED"])
def test_terminal_animals_are_excluded_from_current_herd(monkeypatch, terminal_status):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    animals = _all_category_animals(); animals.append(_animal(f"EXIT-{terminal_status}", terminal_status, "FEMALE", status="INACTIVE", active=False))
    container, _ = _container(animals)
    result = reporting_preview(ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD"), container=container)
    assert result["record_count"] == 6
    assert not any(row["animal_id"] == f"EXIT-{terminal_status}" for row in result["rows"])


def test_animal_register_category_filter_is_canonical(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, _ = _container(_all_category_animals())
    result = reporting_preview(ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD", filters={"category": "Dry Cows"}), container=container)
    assert result["record_count"] == 1
    assert result["rows"][0]["animal_id"] == "DRY-001"
    assert result["rows"][0]["category"] == "Dry"


def test_animal_register_status_filter(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    animals = _all_category_animals(); animals[1].status = "MONITORED"
    container, _ = _container(animals)
    result = reporting_preview(ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD", filters={"status": "MONITORED"}), container=container)
    assert result["record_count"] == 1
    assert result["rows"][0]["animal_id"] == "DRY-001"


def test_animal_population_empty_state_keeps_six_zero_categories(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, _ = _container([])
    result = reporting_preview(ReportingRequest(report_id="animal-population", domain="ANIMALS", period_mode="CURRENT_HERD"), container=container)
    assert result["record_count"] == 6
    assert result["summary"]["total_current_animals"] == 0
    assert all(row["count"] == 0 for row in result["rows"])
    assert result["warnings"] == ["No current Animal Register records match the selected filters."]


def test_animal_register_empty_state_does_not_broaden_query(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, repository = _container(_all_category_animals())
    result = reporting_preview(ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD", filters={"status": "DOES-NOT-EXIST"}), container=container)
    assert repository.get_all_calls == 1
    assert result["record_count"] == 0
    assert result["rows"] == []
    assert result["summary"]["total_current_animals"] == 0


def test_invalid_animal_category_filter_is_rejected(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, _ = _container(_all_category_animals())
    with pytest.raises(Exception) as exc_info:
        reporting_preview(ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD", filters={"category": "Exited"}), container=container)
    assert getattr(exc_info.value, "status_code", None) == 422


def test_preview_generated_at_uses_timezone_aware_farm_authority(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, _ = _container([])
    result = reporting_preview(ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD"), container=container)
    generated = datetime.fromisoformat(result["generated_at"])
    assert generated.tzinfo is not None
    assert generated.utcoffset() == timedelta(hours=5)
    assert result["period"]["as_of_date"] == "2026-09-15"


def test_daily_milk_is_now_linked_to_authoritative_reporting_dataset(monkeypatch):
    monkeypatch.setattr("dairyos.api.reporting.OperationalDateAuthority", _FixedOperationalDateAuthority)
    container, _ = _container([])
    result = reporting_preview(ReportingRequest(report_id="daily-milk", domain="MILK", period_mode="TODAY"), container=container)
    assert result["dataset_status"] == "AUTHORITATIVE_DATASET"
    assert result["authority_status"] == "AUTHORITY_AVAILABLE"
    assert result["record_count"] == 0
    assert result["rows"] == []
    assert result["summary"]["active_milk_liters"] == 0.0


def test_reporting_animals_source_remains_read_only():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8-sig")
    assert ".commit(" not in source
    assert ".add(" not in source
    assert ".delete(" not in source
    assert ".save(" not in source
    assert ".update(" not in source

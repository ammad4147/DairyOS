from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_health_clinical_log_contract():
    source = text("src/DairyOS.Web/src/components/HealthTab.tsx")
    for heading in (
        "Date",
        "Animal ID",
        "Diagnosis",
        "Severity",
        "Symptoms & Details",
        "Treatment",
        "Withdrawal",
        "Next Check-up",
    ):
        assert f">{heading}<" in source
    assert "Mark Healthy" in source
    assert "Declare Healthy" not in source
    assert "/farm/health-cases/${encodeURIComponent(id)}/resolve" in source
    assert "Type</th>" not in source


def test_sender_settings_use_authenticated_backend_contract():
    frontend = text("src/DairyOS.Web/src/components/SettingsTab.tsx")
    backend = text("src/dairyos/api/settings.py")
    assert "/auth/login" in frontend
    assert "Authorization" in frontend
    assert "Bearer ${token}" in frontend
    assert 'require_permission("settings.email")' in backend


def test_coml_selected_period_does_not_borrow_official_monthly_costs():
    frontend = text("src/DairyOS.Web/src/components/COML.tsx")
    backend = text("src/dairyos/api/coml.py")
    assert "Official Backend COML (monthly lock — reference only)" in frontend
    assert "if (officialRec) return" not in frontend
    assert "production_date" in backend
    assert "total_yield" in backend
    assert "is_expense(item)" in backend
    assert "feed_per_l = (feed_total / liters) if liters > 0 else None" in backend


def test_milk_analytics_are_derived_from_persisted_production():
    source = text("src/dairyos/api/milk_production_analytics.py")
    assert "def _yield_drop_watchlist" in source
    assert "def _production_extremes" in source
    assert "DERIVED_LIVE" in source
    assert "if snapshot and float(snapshot.get(\"total_litres\") or 0.0) > 0" in source
    assert "get_open_by_module(\"MILK\")" not in source


def test_dashboard_uses_same_authoritative_milk_analytics():
    source = text("src/dairyos/api/dashboard.py")
    assert "_yield_drop_watchlist(" in source
    assert "_production_extremes(" in source
    assert 'get_open_by_module("MILK")' not in source
    assert "MILK_DAILY_DROP:" not in source
    assert '"production_extremes": production_extremes' in source


def test_milk_disposition_capacity_has_overall_inventory_fallback():
    service = text("src/dairyos/farm/production/services/milk_reconciliation_service.py")
    edit_api = text("src/dairyos/api/milk_traceability.py")
    assert "overall_saleable_capacity" in service
    assert "available_saleable_litres" in service
    assert "overall saleable production" in service
    assert "MilkReconciliationService.validate_disposition_quantity(" in edit_api
    assert "exclude_id=item.id" in edit_api


def test_monthly_milk_sold_reads_authoritative_sold_dispositions():
    frontend = text("src/DairyOS.Web/src/components/MilkTab.tsx")
    assert "const monthSold" in frontend
    assert "monthDispositionRows" in frontend
    assert "row.disposition_type ===" in frontend
    assert "'SOLD'" in frontend
    assert "row.status !== 'VOID'" in frontend

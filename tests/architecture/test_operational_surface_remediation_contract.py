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


def test_sender_settings_are_visible_without_auth_and_navigation_is_protected():
    settings_tab = text("src/DairyOS.Web/src/components/SettingsTab.tsx")
    navigation = text("src/DairyOS.Web/src/components/NavigationVisibilityControl.tsx")
    backend = text("src/dairyos/api/settings.py")
    email_block = backend[backend.index('@router.get("/email")'):]
    assert 'require_permission("settings.email")' not in email_block
    assert "NavigationVisibilityControl" in settings_tab
    assert "Navigation Visibility" in navigation
    assert "/auth/login" in navigation
    assert "Authorization" in navigation
    assert "Bearer ${token}" in navigation
    assert 'require_permission("settings.navigation")' in backend


def test_coml_selected_period_does_not_borrow_official_monthly_costs():
    frontend = text(
        "src/DairyOS.Web/src/components/COML.tsx"
    )
    backend = text(
        "src/dairyos/api/coml.py"
    )
    milk_authority = text(
        "src/dairyos/api/tmr.py"
    )

    # The selected-period Auto calculation remains independent of the
    # persisted official monthly management benchmark. The official value is
    # loaded and displayed as reference/status, not substituted into Auto.
    assert "/farm/coml/integrated" in frontend
    assert "`${API_BASE}/farm/coml?${officialQuery}`" in frontend
    assert "Official COP is the persisted management benchmark used by the Dashboard." in frontend
    assert "if (officialRec) return" not in frontend

    # Milk-period authority is shared through
    # milk_litres_for_period().
    assert "milk_litres_for_period(" in backend
    assert "production_date" in milk_authority
    assert "total_yield" in milk_authority

    assert "is_expense(item)" in backend
    assert "feed_total / liters" in backend
    assert "if liters > 0" in backend


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

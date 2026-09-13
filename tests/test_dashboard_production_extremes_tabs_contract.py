from pathlib import Path


def test_dashboard_has_frequency_tabs_inside_existing_production_extremes_surface():
    source = Path("src/DairyOS.Web/src/components/UnifiedDashboard.tsx").read_text(encoding="utf-8")
    assert "Thrice Milking" in source
    assert "Twice Milking" in source
    assert "productionExtremesFrequency" in source
    assert "THRICE_DAILY" in source
    assert "TWICE_DAILY" in source
    assert 'title="Highest" rows={displayedTop}' in source
    assert 'title="Lowest" rows={displayedBottom}' in source


def test_dashboard_client_maps_both_frequency_cohorts():
    source = Path("src/DairyOS.Web/src/api/commandDashboardClient.ts").read_text(encoding="utf-8")
    assert "productionExtremes.cohorts?.THRICE_DAILY?.highest" in source
    assert "productionExtremes.cohorts?.TWICE_DAILY?.highest" in source
    assert "productionExtremes.cohorts?.THRICE_DAILY?.lowest" in source
    assert "productionExtremes.cohorts?.TWICE_DAILY?.lowest" in source

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DASHBOARD = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "UnifiedDashboard.tsx"
)


def test_dashboard_renders_backend_derived_yield_drop_watchlist():
    text = DASHBOARD.read_text(
        encoding="utf-8"
    )

    assert "data?.yieldDropWatchlist" in text
    assert "persistedDropAlerts" in text
    assert "derivedDropAlerts" in text
    assert "activeDropAlerts = [" in text
    assert "...persistedDropAlerts" in text
    assert "...derivedDropAlerts" in text


def test_persisted_findings_take_precedence_over_derived_duplicates():
    text = DASHBOARD.read_text(
        encoding="utf-8"
    )

    assert "persistedDropAnimalIds" in text
    assert "!persistedDropAnimalIds.has(animalId)" in text


def test_derived_yield_drop_remains_actionable_without_persisted_finding():
    text = DASHBOARD.read_text(
        encoding="utf-8"
    )

    assert "openPassportHandler(animalId)" in text
    assert "setSelectedDropAlertId(alert.id)" in text

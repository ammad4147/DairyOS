from pathlib import Path

from dairyos.api.dashboard import _herd_metrics


ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "src" / "DairyOS.Web" / "src" / "api" / "commandDashboardClient.ts"
DASHBOARD = (
    ROOT / "src" / "DairyOS.Web" / "src" / "components" / "UnifiedDashboard.tsx"
)


def test_dashboard_average_yield_uses_liters_and_governed_herd_denominators():
    composition = [
        {"name": "Milking", "value": 20},
        {"name": "Dry", "value": 5},
        {"name": "Heifer", "value": 10},
        {"name": "Female Calf", "value": 8},
        {"name": "Male Calf", "value": 5},
        {"name": "Bull", "value": 2},
    ]

    metrics = _herd_metrics(
        composition,
        daily_milk_liters=500.0,
    )

    assert metrics == {
        "average_yield_milking_animals_liters": 25.0,
        "average_yield_total_herd_liters": 10.0,
    }


def test_dashboard_average_yield_zero_denominators_are_not_fabricated():
    metrics = _herd_metrics(
        [],
        daily_milk_liters=0.0,
    )

    assert metrics == {
        "average_yield_milking_animals_liters": None,
        "average_yield_total_herd_liters": None,
    }


def test_dashboard_operator_surface_uses_new_names_and_liter_units():
    client = CLIENT.read_text(encoding="utf-8-sig")
    dashboard = DASHBOARD.read_text(encoding="utf-8-sig")

    assert "averageYieldMilkingAnimalsLiters" in client
    assert "averageYieldTotalHerdLiters" in client

    assert 'label="Average Yield (Milking Animals)"' in dashboard
    assert 'label="Average Yield (Total Herd)"' in dashboard

    assert "averageYieldMilkingAnimals" in dashboard
    assert "averageYieldTotalHerd" in dashboard

    assert "Wet Average Yield" not in dashboard
    assert "Dry Average Yield" not in dashboard
    assert "wetAverageYieldPercentage" not in client
    assert "dryAverageYieldPercentage" not in client


def test_dashboard_average_yield_contract_has_no_percentage_authority():
    client = CLIENT.read_text(encoding="utf-8-sig")
    dashboard = DASHBOARD.read_text(encoding="utf-8-sig")

    assert "wet_average_yield_percentage" not in client
    assert "dry_average_yield_percentage" not in client
    assert "average_yield_milking_animals_liters" in client
    assert "average_yield_total_herd_liters" in client

    assert (
        "Number(data.herdMetrics.averageYieldMilkingAnimalsLiters).toFixed(2)} L"
        in dashboard
    )
    assert (
        "Number(data.herdMetrics.averageYieldTotalHerdLiters).toFixed(2)} L"
        in dashboard
    )

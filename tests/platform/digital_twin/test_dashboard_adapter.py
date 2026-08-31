from dairyos.platform.digital_twin.presentation.services.dashboard_adapter import (
    DashboardAdapter,
)


def test_dashboard_generation():

    adapter = DashboardAdapter()

    dashboard = adapter.build(
        farm_id="farm001",
        current_state={
            "milk": 625,
        },
        forecasts={
            "milk": 650,
        },
        scenarios={
            "name": "feed increase",
            "parameter": "feed_cost",
            "change_percent": 15,
            "projected_value": 718.75,
            "variance": 93.75,
            "risk_level": "medium",
        },
        signals=[
            "feed_review",
        ],
    )

    assert dashboard.farm_id == "farm001"
    assert dashboard.current_state["milk"] == 625
    assert dashboard.forecast_summary["milk"] == 650
    assert dashboard.scenario_summary["change_percent"] == 15
    assert dashboard.scenario_summary["risk_level"] == "medium"
    assert len(dashboard.decision_signals) == 1

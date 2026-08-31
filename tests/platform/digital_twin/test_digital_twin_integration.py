from dairyos.platform.digital_twin.services.digital_twin_service import (
    DigitalTwinService,
)


def test_complete_digital_twin_flow():

    service = DigitalTwinService()

    dashboard = service.process(
        farm_id="trident",
        state={
            "milking_cows": 25,
            "milk_daily": 625,
        },
        metric="milk",
        current_value=625,
        scenario_name="milk price reduction",
        parameter="milk_price",
        change_percent=-10,
    )

    assert dashboard.farm_id == "trident"
    assert dashboard.current_state["milk_daily"] == 625
    assert dashboard.scenario_summary["projected_value"] == 562.5
    assert dashboard.scenario_summary["risk_level"] == "low"
    assert len(dashboard.decision_signals) == 1

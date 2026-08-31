from dairyos.platform.digital_twin.services.digital_twin_service import (
    DigitalTwinService,
)


def test_enterprise_digital_twin_service():

    service = DigitalTwinService()

    dashboard = service.process(
        farm_id="farm001",
        state={
            "animals": 50,
        },
        metric="milk",
        current_value=625,
        scenario_name="feed increase",
        parameter="feed",
        change_percent=10,
    )

    assert dashboard.farm_id == "farm001"
    assert dashboard.current_state["animals"] == 50
    assert dashboard.scenario_summary["projected_value"] == 687.5
    assert len(dashboard.decision_signals) == 1

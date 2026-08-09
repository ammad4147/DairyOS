from dairyos.intelligence.integration.executive_runtime_service import (
    ExecutiveRuntimeService,
)


def test_executive_runtime_service_execution():

    service = ExecutiveRuntimeService()


    result = service.execute(
        []
    )


    assert "session" in result

    assert "dashboard" in result

    assert "executive_summary" in result

    assert "cockpit" in result

    assert "command_center" in result



def test_executive_runtime_service_command_center_identity():

    service = ExecutiveRuntimeService()


    result = service.execute(
        []
    )


    command_center = result[
        "command_center"
    ]


    assert command_center.farm_name == "Trident Dairies"

    assert command_center.time_horizon == "current_cycle"

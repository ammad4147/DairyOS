from dairyos.intelligence.api.executive_api import (
    ExecutiveAPI,
)



def test_executive_api_execution():

    api = ExecutiveAPI()


    result = api.execute(
        []
    )


    assert "session" in result

    assert "command_center" in result



def test_executive_api_command_center():

    api = ExecutiveAPI()


    command_center = api.get_command_center(
        []
    )


    assert command_center.farm_name == "Trident Dairies"

    assert command_center.time_horizon == "current_cycle"

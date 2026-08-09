from dairyos.intelligence.api.command_center_api import (
    CommandCenterAPI,
)


def test_command_center_api_execution():

    api = CommandCenterAPI()

    result = api.execute_cycle(
        {}
    )

    assert result is not None

    assert "status" in result

    assert "component" in result

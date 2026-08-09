from dairyos.farm.operations.dashboard import (
    FarmCommandCenterService,
)

from dairyos.farm.operations.services import (
    FarmDashboardService,
)



def test_command_center_builds():

    service = FarmCommandCenterService(
        FarmDashboardService()
    )


    result = service.build()


    assert result.milk_today == 0

    assert result.operational_status == "normal"

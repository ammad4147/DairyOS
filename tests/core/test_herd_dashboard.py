from dairyos.herd.dashboard.models import HerdDashboard

from dairyos.herd.dashboard.services.kpi_service import HerdKPIService



def test_dashboard_creation():


    dashboard = HerdDashboard(

        farm_name="Trident Dairies",

        total_animals=50,

        milking_cows=25,

        dry_cows=5,

        heifers=15,

        calves=5,

        capacity=50

    )


    assert dashboard.total_animals == 50



def test_capacity_utilization():


    service = HerdKPIService()


    result = service.utilization(

        50,

        50

    )


    assert result == 100



def test_milking_ratio():


    service = HerdKPIService()


    result = service.milking_ratio(

        25,

        50

    )


    assert result == 50

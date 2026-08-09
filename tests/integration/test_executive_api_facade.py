from dairyos.intelligence.api.executive_api import (
    ExecutiveAPI,
)



def test_executive_api_intelligence_execution():


    api = ExecutiveAPI()


    result = api.execute_intelligence(
        []
    )


    assert "runtime" in result

    assert "decision" in result

    assert "report" in result



def test_executive_api_report_access():


    api = ExecutiveAPI()


    report = api.get_report(
        []
    )


    assert report.farm_name == "Trident Dairies"

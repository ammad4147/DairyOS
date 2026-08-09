from dairyos.intelligence.application.executive_intelligence_facade import (
    ExecutiveIntelligenceFacade,
)



def test_executive_intelligence_facade_execution():


    facade = ExecutiveIntelligenceFacade()


    result = facade.execute(
        []
    )


    assert "runtime" in result

    assert "decision" in result

    assert "report" in result



def test_executive_intelligence_facade_report_identity():


    facade = ExecutiveIntelligenceFacade()


    result = facade.execute(
        []
    )


    report = result["report"]


    assert report.farm_name == "Trident Dairies"

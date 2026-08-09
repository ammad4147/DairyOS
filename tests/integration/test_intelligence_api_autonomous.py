from dairyos.intelligence.api.intelligence_api import (
    IntelligenceAPI,
)


def test_intelligence_api_autonomous_status():

    api = IntelligenceAPI()

    result = api.get_autonomous_status()

    assert (
        result["component"]
        == "autonomous_runtime_query"
    )

    assert (
        result["status"]
        == "operational"
    )

from dairyos.intelligence.services.intelligence_query_service import (
    IntelligenceQueryService,
)


class FakeRuntime:

    def evaluate_state(
        self,
        state,
    ):

        return {

            "signals": [],

            "recommendations": [],

        }



def test_intelligence_query_returns_summary():

    service = IntelligenceQueryService(
        FakeRuntime()
    )


    result = (
        service
        .get_current_intelligence()
    )


    assert result.signal_count == 0

    assert result.recommendations == []

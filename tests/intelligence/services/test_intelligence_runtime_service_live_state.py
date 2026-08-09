from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)

from dairyos.intelligence.services.intelligence_runtime_service import (
    IntelligenceRuntimeService,
)



def test_runtime_service_evaluates_live_state():

    state = FarmOperationalState(

        farm_id="TRIDENT-DAIRIES",

        operational_date="2026-07-30",

    )


    result = (
        IntelligenceRuntimeService()
        .evaluate_state(state)
    )


    assert (
        "signals"
        in result
    )


    assert (
        "recommendations"
        in result
    )

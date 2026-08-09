from dairyos.intelligence.services.intelligence_runtime_service import (
    IntelligenceRuntimeService,
)

from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)



def test_runtime_service_evaluates_operational_state():

    state = FarmOperationalState(
        farm_id="TRIDENT-DAIRIES",
        operational_date="2026-07-30",
    )


    result = (
        IntelligenceRuntimeService()
        .evaluate_state(state)
    )


    assert "signals" in result

    assert "analysis" in result

    assert "recommendations" in result



def test_runtime_service_does_not_change_state():

    state = FarmOperationalState(
        farm_id="TRIDENT-DAIRIES",
        operational_date="2026-07-30",
    )


    before = state.summary()


    IntelligenceRuntimeService().evaluate_state(
        state
    )


    after = state.summary()


    assert before == after

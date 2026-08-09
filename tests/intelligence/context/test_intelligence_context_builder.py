from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)

from dairyos.intelligence.context.intelligence_context_builder import (
    IntelligenceContextBuilder,
)



def test_context_builder_reads_operational_state():

    state = FarmOperationalState(

        farm_id="TRIDENT-DAIRIES",

        operational_date="2026-07-30",

    )


    context = (
        IntelligenceContextBuilder()
        .build(state)
    )


    assert (
        context["farm_id"]
        ==
        "TRIDENT-DAIRIES"
    )


    assert (
        "milk_total"
        in context
    )



def test_context_builder_does_not_mutate_state():

    state = FarmOperationalState(

        farm_id="TRIDENT-DAIRIES",

        operational_date="2026-07-30",

    )


    before = state.summary()


    (
        IntelligenceContextBuilder()
        .build(state)
    )


    after = state.summary()


    assert before == after

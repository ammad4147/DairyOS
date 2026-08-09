from dairyos.intelligence.context.operational_context_builder import (
    OperationalContextBuilder,
)

from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)



def test_context_builder_reads_operational_state():

    state = FarmOperationalState(
        farm_id="TRIDENT-DAIRIES",
        operational_date="2026-07-30",
    )


    context = (
        OperationalContextBuilder()
        .build(state)
    )


    assert (
        context["farm_id"]
        ==
        "TRIDENT-DAIRIES"
    )


    assert (
        context["milk_total"]
        ==
        0
    )


    assert (
        context["operational_status"]
        ==
        "normal"
    )



def test_context_builder_does_not_mutate_state():

    state = FarmOperationalState(
        farm_id="TRIDENT-DAIRIES",
        operational_date="2026-07-30",
    )


    before = state.summary()


    OperationalContextBuilder().build(
        state
    )


    after = state.summary()


    assert before == after

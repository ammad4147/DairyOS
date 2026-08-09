from dairyos.intelligence.operations.services.farm_situation_service import (
    FarmSituationService,
)

from dairyos.intelligence.operations.services.farm_decision_service import (
    FarmDecisionService,
)

from dairyos.intelligence.operations.orchestration.services.operations_orchestration_service import (
    OperationsOrchestrationService,
)



def test_farm_condition_creates_operational_actions():


    situation = FarmSituationService().evaluate(

        total_animals=50,

        milking_cows=25,

        dry_cows=10,

        close_up_cows=3,

        animals_requiring_attention=2,

        daily_milk_litres=560,

        previous_day_milk_litres=620,

        feed_cost_per_litre=100,

        reproduction_alerts=1,
    )


    actions = (
        FarmDecisionService()
        .create_actions(
            situation
        )
    )


    orchestration = (
        OperationsOrchestrationService()
    )


    assignment = orchestration.create_assignment(

        actions[0],

        assigned_to="farm_manager",

        assigned_role="supervisor",
    )


    assert len(actions) > 0

    assert actions[0].action_type == (
        "animal_review"
    )

    assert assignment.status == (
        "assigned"
    )

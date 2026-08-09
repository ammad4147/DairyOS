from dairyos.intelligence.operations.services.farm_situation_service import (
    FarmSituationService,
)

from dairyos.intelligence.operations.services.farm_decision_service import (
    FarmDecisionService,
)

from dairyos.intelligence.operations.orchestration.services.operations_orchestration_service import (
    OperationsOrchestrationService,
)



def test_farm_action_lifecycle():

    situation = FarmSituationService().evaluate(

        total_animals=50,

        milking_cows=25,

        dry_cows=8,

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


    service = OperationsOrchestrationService()


    assignment = service.create_assignment(

        actions[0],

        assigned_to="farm_manager",

        assigned_role="supervisor",
    )


    execution = service.record_execution(

        actions[0],

        performed_by="farm_manager",

        notes="Animal health inspection completed",
    )


    outcome = service.create_outcome(

        actions[0],

        result="Animals inspected",

        success=True,

        feedback="No major issues found",
    )


    assert assignment.status == (
        "assigned"
    )


    assert execution.execution_status == (
        "completed"
    )


    assert outcome.success is True

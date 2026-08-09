from dairyos.intelligence.operations.services.farm_situation_service import (
    FarmSituationService,
)

from dairyos.intelligence.operations.health.services.farm_health_service import (
    FarmHealthService,
)

from dairyos.intelligence.operations.health.services.health_action_service import (
    HealthActionService,
)

from dairyos.intelligence.operations.orchestration.services.operations_orchestration_service import (
    OperationsOrchestrationService,
)



def test_health_action_executes_through_farm_workflow():


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


    report = FarmHealthService().evaluate(
        situation
    )


    actions = HealthActionService().create_actions(
        report
    )


    orchestration = OperationsOrchestrationService()


    assignment = orchestration.create_assignment(

        actions[0],

        assigned_to="farm_manager",

        assigned_role="supervisor",
    )


    execution = orchestration.record_execution(

        actions[0],

        performed_by="farm_manager",

        notes="Health review completed",
    )


    outcome = orchestration.create_outcome(

        actions[0],

        result="Animal inspection completed",

        success=True,

        feedback="No emergency condition found",
    )


    assert assignment.status == (
        "assigned"
    )


    assert execution.execution_status == (
        "completed"
    )


    assert outcome.success is True

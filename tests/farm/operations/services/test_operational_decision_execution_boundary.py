from dairyos.farm.operations.runtime.farm_operations_runtime import (
    FarmOperationsRuntime,
)

from dairyos.farm.operations.services.operational_decision_execution_boundary import (
    OperationalDecisionExecutionBoundary,
)



def test_operational_decision_execution_requires_boundary():

    runtime = FarmOperationsRuntime()


    boundary = OperationalDecisionExecutionBoundary(
        runtime
    )


    decision = {

        "decision_id":
            "DEC-001",

        "action":
            "record_milk_activity",

        "details": {

            "animal_id":
                "COW-001",

            "session":
                "MORNING",

            "litres":
                25,

        },

    }


    execution = boundary.execute(
        decision,
        approved_by="Farm Manager",
    )


    assert execution.status == "EXECUTED"


    assert len(
        runtime.events
    ) == 1


    assert (
        runtime.events[0].event_type
        ==
        "milk_recorded"
    )



def test_unsupported_decision_is_not_executed():

    runtime = FarmOperationsRuntime()


    boundary = OperationalDecisionExecutionBoundary(
        runtime
    )


    execution = boundary.execute(

        {
            "decision_id":
                "DEC-002",

            "action":
                "delete_farm_data",

            "details":
                {},

        },

        approved_by="Farm Manager",

    )


    assert execution.status == "REJECTED"


    assert len(
        runtime.events
    ) == 0

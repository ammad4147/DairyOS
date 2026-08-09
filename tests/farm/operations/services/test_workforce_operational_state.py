from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)



def test_workforce_event_updates_operational_state():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="workforce_activity_recorded",

        animal_id=None,

        operator="Farm Manager",

        payload={

            "metric_type": "pending_tasks",

            "value": 5,

        },

    )


    state = service.process_event(
        event
    )


    assert (
        state.workforce_status["pending_tasks"]
        ==
        5
    )



def test_workforce_state_is_in_summary():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="workforce_activity_recorded",

        animal_id=None,

        operator="Farm Manager",

        payload={

            "metric_type": "completion_rate",

            "value": 95,

        },

    )


    summary = service.process_event(
        event
    ).summary()


    assert (
        summary["workforce_status"]["completion_rate"]
        ==
        95
    )

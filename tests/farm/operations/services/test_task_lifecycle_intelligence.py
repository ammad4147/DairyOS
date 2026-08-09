from datetime import datetime, timedelta, timezone

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.services.operational_state_query_service import (
    OperationalStateQueryService,
)



def test_task_creation_enters_operational_state():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(

        event_type="task_created",

        animal_id=None,

        operator="Farm Manager",

        payload={
            "task_id": "TASK-001",
            "title": "Clean water troughs",
            "priority": "HIGH",
        },

    )


    state = service.process_event(
        event
    )


    assert len(
        state.open_tasks
    ) == 1


    assert (
        state.open_tasks[0]["task_id"]
        ==
        "TASK-001"
    )



def test_task_is_available_through_query_layer():

    service = FarmOperationalStateService()


    service.process_event(

        FarmOperationEvent(

            event_type="task_created",

            animal_id=None,

            operator="Manager",

            payload={
                "task_id": "TASK-002",
                "title": "Check feed inventory",
            },

        )

    )


    query = OperationalStateQueryService(
        service
    )


    result = query.get_current_state()


    assert len(
        result.open_tasks
    ) == 1


    assert (
        result.open_tasks[0]["task_id"]
        ==
        "TASK-002"
    )



def test_high_priority_task_generates_heads_up():

    service = FarmOperationalStateService()


    service.process_event(

        FarmOperationEvent(

            event_type="task_created",

            animal_id=None,

            operator="Manager",

            payload={
                "task_id": "TASK-003",
                "priority": "HIGH",
            },

        )

    )


    query = OperationalStateQueryService(
        service
    )


    result = query.get_current_state()


    assert any(

        x["notification_type"]
        ==
        "HIGH_PRIORITY_TASK"

        for x in result.heads_up_notifications

    )



def test_overdue_task_generates_heads_up():

    service = FarmOperationalStateService()


    overdue = (
        datetime.now(timezone.utc)
        -
        timedelta(days=1)
    ).isoformat()


    service.process_event(

        FarmOperationEvent(

            event_type="task_created",

            animal_id=None,

            operator="Manager",

            payload={
                "task_id": "TASK-004",
                "due_date": overdue,
            },

        )

    )


    query = OperationalStateQueryService(
        service
    )


    result = query.get_current_state()


    assert any(

        x["notification_type"]
        ==
        "OVERDUE_TASK"

        for x in result.heads_up_notifications

    )



def test_task_completion_moves_lifecycle():

    service = FarmOperationalStateService()


    service.process_event(

        FarmOperationEvent(

            event_type="task_created",

            animal_id=None,

            operator="Manager",

            payload={
                "task_id": "TASK-005",
            },

        )

    )


    service.process_event(

        FarmOperationEvent(

            event_type="task_completed",

            animal_id=None,

            operator="Manager",

            payload={
                "task_id": "TASK-005",
            },

        )

    )


    state = service.get_state()


    assert len(
        state.completed_tasks
    ) == 1


    assert (
        state.completed_tasks[0]["task_id"]
        ==
        "TASK-005"
    )

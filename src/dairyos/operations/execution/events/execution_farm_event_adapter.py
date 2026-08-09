from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class ExecutionFarmEventAdapter:
    """
    Converts execution lifecycle domain events
    into FarmOperationEvents.

    Domain execution events remain owned by
    execution services.

    FarmOperationEvent becomes the operational
    runtime integration boundary.
    """


    def adapt(
        self,
        event,
    ) -> FarmOperationEvent:

        payload = dict(
            event.payload
        )


        execution_id = (
            payload.get(
                "execution_id"
            )
        )


        operator = (

            payload.get(
                "completed_by"
            )

            or payload.get(
                "verified_by"
            )

            or payload.get(
                "started_by"
            )

            or payload.get(
                "acknowledged_by"
            )

            or payload.get(
                "assigned_to"
            )

            or "SYSTEM"

        )


        return FarmOperationEvent(

            event_type=event.name,

            animal_id=None,

            operator=operator,

            payload=payload,

        )

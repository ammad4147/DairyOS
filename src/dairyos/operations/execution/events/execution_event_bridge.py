from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class ExecutionEventBridge:
    """
    Translates execution lifecycle events
    into enterprise OperationalEvents.

    Execution lifecycle remains a domain concern.

    OperationalEvent becomes the enterprise
    integration boundary.
    """


    def adapt(
        self,
        event,
    ) -> OperationalEvent:

        payload = dict(
            event.payload
        )

        execution_id = (
            payload.get(
                "execution_id"
            )
        )


        actor = (

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


        return OperationalEvent(

            event_type=event.name,

            entity_type="execution",

            entity_id=execution_id,

            actor=actor,

            payload=payload,

        )

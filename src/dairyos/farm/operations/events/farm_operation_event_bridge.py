from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class FarmOperationEventBridge:
    """
    Canonical translation boundary from the farm-operation domain
    into the enterprise OperationalEvent model.

    Architectural contract:

        FarmOperationEvent
                |
                v
        FarmOperationEventBridge
                |
                v
        OperationalEvent

    This class owns the ONE canonical implementation of farm-event
    to enterprise-event translation.

    It does not:
    - publish events
    - persist events
    - invoke subscribers
    - own farm operational state
    - own business workflow rules
    """

    def adapt(
        self,
        event: FarmOperationEvent,
    ) -> OperationalEvent:
        """
        Translate one FarmOperationEvent into one OperationalEvent.

        The source FarmOperationEvent remains unchanged.
        """

        if event is None:
            raise ValueError(
                "FarmOperationEvent is required"
            )

        entity_type = (
            "animal"
            if event.animal_id is not None
            else "farm_operation"
        )

        entity_id = (
            event.animal_id
            if event.animal_id is not None
            else event.event_id
        )

        payload = dict(
            event.payload
        )

        return OperationalEvent(
            event_type=event.event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=event.operator,
            payload=payload,
            timestamp=event.timestamp,
        )

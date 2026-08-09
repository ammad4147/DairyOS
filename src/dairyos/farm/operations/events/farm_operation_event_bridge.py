from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)


class FarmOperationEventBridge:
    """
    Translates farm-domain operational events
    into enterprise OperationalEvents.

    Farm operations remain isolated from
    platform event infrastructure.
    """


    def adapt(
        self,
        event: FarmOperationEvent,
    ) -> OperationalEvent:

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


        return OperationalEvent(

            event_type=event.event_type,

            entity_type=entity_type,

            entity_id=entity_id,

            actor=event.operator,

            payload=event.payload,

            timestamp=event.timestamp,

        )

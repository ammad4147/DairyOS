from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class LifecycleEventBridge:
    """
    Compatibility bridge between lifecycle events
    and DairyOS operational events.

    Flow:

        LifecycleEvent
              |
              v
        FarmOperationEvent
              |
              v
        AnimalEventProjection
              |
              v
        AnimalOperationalState
    """


    def convert(
        self,
        lifecycle_event,
    ) -> FarmOperationEvent:

        return FarmOperationEvent(

            event_type="lifecycle_changed",

            animal_id=lifecycle_event.animal_id,

            operator="SYSTEM",

            payload={

                "previous_status":
                    lifecycle_event.previous_status,

                "new_status":
                    lifecycle_event.new_status,

                "location":
                    lifecycle_event.location,

                "source_event_type":
                    lifecycle_event.event_type,

            },

            timestamp=lifecycle_event.timestamp,

        )

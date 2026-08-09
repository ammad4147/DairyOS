from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.gateway.operational_event_adapter import (
    OperationalEventAdapter,
)


class OperationsEventGateway:
    """
    Converts farm operation events
    into downstream event representations.

    Responsibilities:

    - Farm Day timeline integration
    - Enterprise operational event translation

    Does not own business logic.
    """

    def __init__(
        self,
        farm_day_runtime=None,
        operational_event_adapter=None,
        operational_event_publisher=None,
    ):

        self.farm_day_runtime = (
            farm_day_runtime
        )

        self.operational_event_adapter = (
            operational_event_adapter
            if operational_event_adapter is not None
            else OperationalEventAdapter()
        )

        self.operational_event_publisher = (
            operational_event_publisher
        )


    def publish(
        self,
        event: FarmOperationEvent,
    ):

        timeline_record = {

            "event_type": event.event_type,

            "animal_id": event.animal_id,

            "operator": event.operator,

            "timestamp": event.timestamp,

            "payload": event.payload,

        }


        if self.farm_day_runtime is not None:

            self.farm_day_runtime.record_activity(
                timeline_record
            )


        if self.operational_event_publisher is not None:

            operational_event = (
                self.operational_event_adapter
                .adapt(event)
            )

            self.operational_event_publisher.publish(
                operational_event
            )


        return timeline_record

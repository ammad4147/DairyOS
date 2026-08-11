from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.events.farm_operation_event_bridge import (
    FarmOperationEventBridge,
)


class OperationsEventGateway:
    """
    Application gateway for FarmOperationEvent integration.

    Responsibilities:

    - create Farm Day timeline records
    - translate FarmOperationEvent into OperationalEvent
    - publish the translated enterprise event when a publisher exists

    Architectural contract:

        FarmOperationEvent
                |
                +----------------------+
                |                      |
                v                      v
        Farm Day timeline       FarmOperationEventBus
                |
                |
                v
        FarmOperationEventBridge
                |
                v
        OperationalEventPublisher

    The gateway owns integration orchestration.

    It does not:
    - own farm business state
    - mutate farm operation aggregates
    - perform projections
    - invoke subscribers directly
    - implement execution lifecycle rules

    Compatibility:
    - operational_event_adapter remains accepted
    - operational_event_adapter remains exposed as an attribute
    - event_bridge is the canonical internal name
    """

    def __init__(
        self,
        farm_day_runtime=None,
        operational_event_adapter=None,
        operational_event_publisher=None,
        event_bridge=None,
    ):
        self.farm_day_runtime = (
            farm_day_runtime
        )

        if (
            event_bridge is not None
            and operational_event_adapter is not None
        ):
            raise ValueError(
                "Provide either event_bridge or "
                "operational_event_adapter, not both"
            )

        self.event_bridge = (
            event_bridge
            if event_bridge is not None
            else (
                operational_event_adapter
                if operational_event_adapter is not None
                else FarmOperationEventBridge()
            )
        )

        # Compatibility attribute.
        #
        # Existing callers may still inspect or inject
        # operational_event_adapter.
        self.operational_event_adapter = (
            self.event_bridge
        )

        self.operational_event_publisher = (
            operational_event_publisher
        )

    def publish(
        self,
        event: FarmOperationEvent,
        operational_event_publisher=None,
    ):
        """
        Publish one farm operation through the gateway.

        A publisher supplied directly to this method takes precedence
        over the publisher configured during construction.

        This prevents the runtime from maintaining a second enterprise
        publication path.
        """

        if event is None:
            raise ValueError(
                "FarmOperationEvent is required"
            )

        timeline_record = {
            "event_type": event.event_type,
            "animal_id": event.animal_id,
            "operator": event.operator,
            "timestamp": event.timestamp,
            "payload": dict(event.payload),
        }

        if self.farm_day_runtime is not None:
            self.farm_day_runtime.record_activity(
                timeline_record
            )

        publisher = (
            operational_event_publisher
            if operational_event_publisher is not None
            else self.operational_event_publisher
        )

        if publisher is not None:
            operational_event = (
                self.event_bridge.adapt(
                    event
                )
            )

            publisher.publish(
                operational_event
            )

        return timeline_record

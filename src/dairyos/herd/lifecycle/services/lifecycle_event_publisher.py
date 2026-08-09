from dairyos.farm.herd.services.lifecycle_event_bridge import (
    LifecycleEventBridge,
)


class LifecycleEventPublisher:
    """
    Publishes lifecycle domain events
    into DairyOS farm operational events.

    Adapter only.

    Lifecycle rules remain owned by:
        LifecycleEngine

    Operational state remains owned by:
        AnimalOperationalState projection
    """


    def __init__(
        self,
        event_bus,
        bridge=None,
    ):

        self.event_bus = event_bus

        self.bridge = (
            bridge
            if bridge is not None
            else LifecycleEventBridge()
        )



    def publish(
        self,
        lifecycle_event,
    ):

        farm_event = (
            self.bridge.convert(
                lifecycle_event
            )
        )


        return self.event_bus.publish(
            farm_event
        )

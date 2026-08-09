from datetime import datetime


from dairyos.operations.events.models.event_type import (
    OperationalEventType,
)

from dairyos.operations.events.models.operational_event import (
    OperationalEvent,
)

from dairyos.operations.events.services.event_bus_service import (
    EventBusService,
)



def test_event_publish():

    bus = EventBusService()

    event = OperationalEvent(
        event_type=OperationalEventType.TASK_CREATED,
        source="Operations",
        description="Feed task created",
        created_at=datetime.now(),
    )

    bus.publish(event)

    assert len(bus.history()) == 1



def test_event_subscription():

    bus = EventBusService()

    received = []

    def handler(event):

        received.append(event)


    bus.subscribe(handler)


    bus.publish(
        OperationalEvent(
            event_type=OperationalEventType.TASK_COMPLETED,
            source="Operations",
            description="Task completed",
            created_at=datetime.now(),
        )
    )


    assert len(received) == 1

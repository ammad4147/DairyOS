from dairyos.platform.events.models.operational_event import (
    OperationalEvent,
)



class OperationalEventPublisher:
    """
    Application boundary for publishing
    operational farm events.
    """



    def __init__(
        self,
        store,
        bus,
        dispatcher,
    ):

        self.store = store

        self.bus = bus

        self.dispatcher = dispatcher



    def publish(
        self,
        event: OperationalEvent,
    ):

        self.store.append(
            event
        )


        self.bus.publish(
            event
        )


        self.dispatcher.dispatch(
            event
        )


        return event

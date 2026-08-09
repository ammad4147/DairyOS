class EventDispatcher:
    """
    Dispatches operational events
    to registered subscribers.
    """



    def __init__(
        self,
        registry,
    ):

        self.registry = registry



    def dispatch(
        self,
        event,
    ):

        handlers = self.registry.subscribers_for(
            event.event_type
        )


        for handler in handlers:

            handler(event)


        return len(
            handlers
        )

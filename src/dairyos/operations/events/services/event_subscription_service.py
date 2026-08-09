class EventSubscriptionService:
    """
    Manages event consumers.
    """


    def __init__(self, event_bus):

        self.event_bus = event_bus


    def register(
        self,
        handler,
    ):

        return self.event_bus.subscribe(handler)

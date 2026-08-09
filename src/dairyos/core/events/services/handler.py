class EventHandlerRegistry:


    def __init__(self):

        self.handlers = {}


    def register(
        self,
        event_type,
        handler
    ):

        self.handlers[event_type] = handler


    def handle(self, event):

        handler = self.handlers.get(
            event.event_type
        )

        if handler:
            return handler(event)

        return None

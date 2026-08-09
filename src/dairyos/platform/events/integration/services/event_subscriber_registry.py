from dairyos.platform.events.integration.models.event_subscription import (
    EventSubscription,
)



class EventSubscriberRegistry:
    """
    Registry for operational event listeners.
    """



    def __init__(self):

        self.subscriptions = []



    def register(
        self,
        event_type,
        handler,
    ):

        subscription = EventSubscription(

            event_type=event_type,

            handler=handler,

        )


        self.subscriptions.append(
            subscription
        )


        return subscription



    def subscribers_for(
        self,
        event_type,
    ):

        return [

            item.handler

            for item in self.subscriptions

            if item.event_type == event_type

        ]

from dairyos.platform.events.models.event import Event



class EventBridge:
    """
    Connects operational domains to enterprise event bus.
    """



    def __init__(
        self,
        event_bus,
    ):

        self.event_bus = event_bus



    def publish_domain_event(
        self,
        domain: str,
        event_name: str,
        payload: dict,
    ):


        event = Event(

            name=event_name,

            payload={

                "domain": domain,

                **payload,

            },

        )


        return self.event_bus.publish(
            event
        )

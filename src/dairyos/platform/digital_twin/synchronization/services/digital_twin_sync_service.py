from dairyos.platform.digital_twin.synchronization.models.synchronization_event import (
    SynchronizationEvent,
)



class DigitalTwinSyncService:
    """
    Synchronizes operational events into
    digital twin state.
    """



    def __init__(self):

        self.events = []



    def synchronize(

        self,

        source,

        event_type,

        entity_id,

        payload,

    ):


        event = SynchronizationEvent(

            source=source,

            event_type=event_type,

            entity_id=entity_id,

        )


        self.events.append(

            {

                "event": event,

                "payload": payload,

            }

        )


        return event



    def history(self):

        return self.events


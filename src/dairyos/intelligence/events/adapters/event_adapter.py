class EventAdapter:
    """
    Enterprise event adapter boundary.

    Converts enterprise events into
    persistence-compatible representations.

    Initial implementation remains
    persistence independent.
    """


    def adapt(
        self,
        event,
    ):

        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "actor": event.actor,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "severity": event.severity,
            "correlation_id": event.correlation_id,
            "timestamp": event.timestamp,
            "payload": event.payload,
        }

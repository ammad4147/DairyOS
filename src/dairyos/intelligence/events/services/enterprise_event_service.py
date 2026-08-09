from dairyos.intelligence.events.models.enterprise_event import (
    EnterpriseEvent,
)


class EnterpriseEventService:
    """
    Enterprise event creation boundary.

    Responsible for:

    - creating standardized events
    - assigning event identity
    - maintaining correlation metadata

    Does not persist events.
    """


    def create_event(
        self,
        event_type: str,
        source: str,
        actor: str,
        entity_type: str,
        entity_id: str,
        payload: dict,
        severity: str = "normal",
        correlation_id: str | None = None,
    ):

        event = EnterpriseEvent(
            event_type=event_type,
            source=source,
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            severity=severity,
        )


        if correlation_id:

            event.correlation_id = (
                correlation_id
            )


        return event

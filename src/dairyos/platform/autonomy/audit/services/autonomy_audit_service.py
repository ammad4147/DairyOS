from dairyos.platform.autonomy.audit.models.autonomy_audit_event import (
    AutonomyAuditEvent,
)



class AutonomyAuditService:
    """
    Records autonomous intelligence history.
    """



    def __init__(self):

        self.events = []



    def record(

        self,

        event_type,

        entity_type,

        entity_id,

        actor,

        details,

    ):


        event = AutonomyAuditEvent(

            event_type=event_type,

            entity_type=entity_type,

            entity_id=entity_id,

            actor=actor,

            details=details,

        )


        self.events.append(event)


        return event



    def history(self):

        return self.events


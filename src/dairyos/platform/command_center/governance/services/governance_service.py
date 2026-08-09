from dairyos.platform.command_center.governance.models.command_audit_record import (
    CommandAuditRecord,
)



class GovernanceService:
    """
    Provides Command Center authorization and audit support.
    """



    def __init__(self):

        self.audit_records = []



    def authorize(
        self,
        actor,
        permission,
    ):

        return True



    def record_action(
        self,
        actor_id,
        action,
        entity_type,
        entity_id,
        result,
    ):


        record = CommandAuditRecord(

            actor_id=actor_id,

            action=action,

            entity_type=entity_type,

            entity_id=entity_id,

            result=result,

        )


        self.audit_records.append(record)


        return record


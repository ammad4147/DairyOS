from dairyos.platform.audit.models.audit_record import (
    AuditRecord,
)



class AuditService:
    """
    Enterprise operational audit service.
    """



    def __init__(self):

        self.records = []



    def record(
        self,
        audit_record: AuditRecord,
    ):


        self.records.append(

            audit_record

        )


        return audit_record



    def history(self):

        return self.records



    def entity_history(
        self,
        entity_type,
        entity_id,
    ):


        return [

            record

            for record in self.records

            if (

                record.entity_type == entity_type

                and

                record.entity_id == entity_id

            )

        ]


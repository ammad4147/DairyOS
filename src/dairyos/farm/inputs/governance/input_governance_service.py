from dairyos.farm.inputs.governance.input_audit_record import (
    OperationalInputAuditRecord,
)


class InputGovernanceService:
    """
    Provides accountability and audit tracking
    for operational inputs.
    """


    def __init__(self):

        self.records = []



    def record(
        self,
        event,
        accepted=True,
    ):

        record = OperationalInputAuditRecord(

            input_type=
                event.input_type,

            actor=
                event.actor,

            source=
                event.source,

            accepted=
                accepted,

        )


        self.records.append(
            record
        )


        return record



    def list_records(
        self,
    ):

        return list(
            self.records
        )

from dairyos.farm.inputs.models.operational_input_record import (
    OperationalInputRecord,
)


class OperationalInputCaptureService:
    """
    Captures farm operational inputs.

    This service creates the controlled boundary between
    human/device input and DairyOS operational processing.
    """

    def __init__(
        self,
        registry=None,
    ):

        self.registry = registry

        self.records = []


    def capture(
        self,
        input_type: str,
        payload: dict,
        source: str,
        actor: str,
    ):

        record = OperationalInputRecord(
            input_type=input_type,
            payload=payload,
            source=source,
            actor=actor,
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

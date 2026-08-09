from dairyos.farm.inputs.models.input_command import (
    OperationalInputCommand,
)


class OperationalInputCommandService:
    """
    Application boundary for operational inputs.
    """

    def __init__(
        self,
        ingestion_service,
    ):

        self.ingestion_service = ingestion_service



    def submit(
        self,
        command: OperationalInputCommand,
    ):

        return self.ingestion_service.ingest(
            input_type=command.input_type,
            payload=command.payload,
            source=command.source,
            actor=command.actor,
        )


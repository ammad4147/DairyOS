from dairyos.farm.inputs.models.input_command import (
    OperationalInputCommand,
)


class FarmInputGateway:
    """
    Human-friendly farm operational input gateway.

    Provides explicit operational entry points for all recognized
    farm activities while also exposing one canonical submission
    method for API/UI adapters.

    The gateway is deliberately thin: command creation and
    processing remain owned by the canonical operational input
    command service supplied by ApplicationRuntime.
    """

    def __init__(
        self,
        command_service,
    ):

        if command_service is None:
            raise ValueError(
                "FarmInputGateway requires an operational input command service."
            )

        self.command_service = command_service

    def record(
        self,
        input_type,
        payload,
        actor,
    ):

        return self._submit(
            input_type,
            payload,
            actor,
        )

    def _submit(
        self,
        input_type,
        payload,
        actor,
    ):

        return self.command_service.submit(
            OperationalInputCommand(
                input_type=input_type,
                payload=payload,
                source="farm_operator",
                actor=actor,
            )
        )

    def record_milk(self, payload, actor):

        return self._submit(
            "milk_production",
            payload,
            actor,
        )

    def record_feed(self, payload, actor):

        return self._submit(
            "feeding",
            payload,
            actor,
        )

    def record_health(self, payload, actor):

        return self._submit(
            "animal_health",
            payload,
            actor,
        )

    def record_breeding(self, payload, actor):

        return self._submit(
            "breeding",
            payload,
            actor,
        )

    def record_workforce(self, payload, actor):

        return self._submit(
            "workforce",
            payload,
            actor,
        )

    def record_inventory(self, payload, actor):

        return self._submit(
            "inventory",
            payload,
            actor,
        )

    def record_equipment(self, payload, actor):

        return self._submit(
            "equipment",
            payload,
            actor,
        )

    def record_financial(self, payload, actor):

        return self._submit(
            "financial",
            payload,
            actor,
        )

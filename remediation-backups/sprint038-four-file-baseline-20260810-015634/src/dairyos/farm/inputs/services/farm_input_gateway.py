from dairyos.farm.inputs.models.input_command import (
    OperationalInputCommand,
)


class FarmInputGateway:
    """
    Human-friendly farm operational input gateway.

    Provides explicit operational entry points for all recognized
    farm activities while also exposing one canonical submission
    method for API/UI adapters.
    """

    def __init__(
        self,
        command_service,
    ):
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
        return self._submit("milk_production", payload, actor)

    def record_feed(self, payload, actor):
        return self._submit("feeding", payload, actor)

    def record_health(self, payload, actor):
        return self._submit("animal_health", payload, actor)

    def record_breeding(self, payload, actor):
        return self._submit("breeding", payload, actor)

    def record_workforce(self, payload, actor):
        return self._submit("workforce", payload, actor)

    def record_inventory(self, payload, actor):
        return self._submit("inventory", payload, actor)

    def record_equipment(self, payload, actor):
        return self._submit("equipment", payload, actor)

    def record_financial(self, payload, actor):
        return self._submit("financial", payload, actor)

from dairyos.farm.inputs.models.input_definition import (
    OperationalInputDefinition,
)


class OperationalInputValidationService:
    """
    Validates operational input definitions
    before registration.
    """

    def validate(
        self,
        definition: OperationalInputDefinition,
    ):

        errors = []

        if not definition.input_type:
            errors.append(
                "input_type missing"
            )

        if not definition.name:
            errors.append(
                "name missing"
            )

        if not definition.description:
            errors.append(
                "description missing"
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

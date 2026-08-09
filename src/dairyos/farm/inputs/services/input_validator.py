from dairyos.farm.inputs.models.validation_result import (
    OperationalInputValidationResult,
)


class OperationalInputValidator:
    """
    Validates operational inputs before
    they enter DairyOS event flow.
    """

    def validate(
        self,
        definition,
        payload,
    ):

        if definition is None:

            return OperationalInputValidationResult(
                valid=False,
                message="Unknown operational input type",
            )


        if payload is None:

            return OperationalInputValidationResult(
                valid=False,
                message="Input payload cannot be empty",
            )


        if not isinstance(
            payload,
            dict,
        ):

            return OperationalInputValidationResult(
                valid=False,
                message="Input payload must be a dictionary",
            )


        return OperationalInputValidationResult(
            valid=True,
            message="Validated",
        )


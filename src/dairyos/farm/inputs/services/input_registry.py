from dairyos.farm.inputs.models.input_definition import (
    OperationalInputDefinition,
)


class OperationalInputRegistry:
    """
    Central registry for all farm operational inputs.

    The registry is the authoritative catalogue
    of operational input contracts accepted by DairyOS.
    """

    def __init__(self):

        self._inputs = {}


    def register(
        self,
        definition: OperationalInputDefinition,
    ):

        self._inputs[
            definition.input_type
        ] = definition

        return definition



    def exists(
        self,
        input_type: str,
    ) -> bool:

        return (
            input_type
            in self._inputs
        )



    def get(
        self,
        input_type: str,
    ):

        return self._inputs.get(
            input_type
        )



    def validate(
        self,
        input_type: str,
        payload: dict | None = None,
    ):

        if not self.exists(
            input_type
        ):

            raise ValueError(
                f"Unknown operational input type: {input_type}"
            )


        definition = self.get(
            input_type
        )


        if payload is None:
            return True


        missing_fields = [
            field
            for field in definition.required_fields
            if field not in payload
        ]


        if missing_fields:

            raise ValueError(
                {
                    "message":
                        "Operational input contract violation",
                    "input_type":
                        input_type,
                    "missing_fields":
                        missing_fields,
                }
            )


        return True



    def list_inputs(
        self,
    ):

        return list(
            self._inputs.values()
        )

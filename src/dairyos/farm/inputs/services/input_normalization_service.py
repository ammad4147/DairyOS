from dairyos.farm.inputs.services.input_registry import (
    OperationalInputRegistry,
)


class InputNormalizationService:
    """
    Normalizes incoming operational farm inputs
    before contract validation.

    Responsibilities:

    Raw operational payload
            |
            v
    Canonical operational payload

    Examples:

    quantity -> quantity_kg
    milk session yields -> total_yield
    """

    def __init__(
        self,
        registry: OperationalInputRegistry,
    ):

        self.registry = registry



    def normalize(
        self,
        input_type: str,
        payload: dict,
    ):

        if not payload:

            return payload


        definition = (
            self.registry.get(
                input_type
            )
        )


        if not definition:

            return payload



        normalized = dict(
            payload
        )


        if (
            definition.normalization_enabled
            and definition.field_aliases
        ):

            for canonical, aliases in (
                definition.field_aliases.items()
            ):

                if canonical in normalized:

                    continue


                for alias in aliases:

                    if alias in normalized:

                        normalized[canonical] = (
                            normalized.pop(alias)
                        )

                        break



        if input_type == "milk_production":

            yields = [

                normalized.get(
                    "morning_yield",
                    0,
                ),

                normalized.get(
                    "afternoon_yield",
                    0,
                ),

                normalized.get(
                    "evening_yield",
                    0,
                ),

            ]


            if (
                "total_yield"
                not in normalized
            ):

                normalized["total_yield"] = sum(
                    yields
                )



        return normalized

"""
DairyOS Autonomous Runtime Contract

Defines validation rules for autonomous intelligence cycles.
"""


class AutonomousRuntimeContract:
    """
    Validates autonomous decision loop outputs.

    Ensures the runtime boundary
    remains predictable for enterprise consumers.
    """


    REQUIRED_RUNTIME_FIELDS = [
        "status",
        "cycle_id",
        "started_at",
        "completed_at",
        "stages",
        "stage_count",
    ]


    OPTIONAL_PIPELINE_FIELDS = [
        "prediction",
        "decision",
        "command",
        "execution",
        "memory",
        "learning",
    ]


    def validate(
        self,
        result: dict,
    ) -> bool:
        """
        Validate autonomous runtime result.
        """

        if not isinstance(
            result,
            dict,
        ):
            return False


        runtime = result.get(
            "runtime"
        )


        if runtime is None:

            return False


        for field in self.REQUIRED_RUNTIME_FIELDS:

            if field not in runtime:

                return False


        if runtime["status"] != "completed":

            return False


        if runtime["stage_count"] != len(
            runtime["stages"]
        ):

            return False


        return True



    def missing_fields(
        self,
        result: dict,
    ) -> list:

        missing = []


        if not isinstance(
            result,
            dict,
        ):
            return self.REQUIRED_RUNTIME_FIELDS


        runtime = result.get(
            "runtime",
            {},
        )


        for field in self.REQUIRED_RUNTIME_FIELDS:

            if field not in runtime:

                missing.append(
                    field
                )


        return missing

class HealthManagementService:
    """
    Handles animal health operations.
    """



    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def record_observation(
        self,
        record,
    ):

        return self.repository.save_health(
            record
        )



    def record_treatment(
        self,
        treatment,
    ):

        return self.repository.save_treatment(
            treatment
        )



    def animals_needing_attention(
        self,
    ):

        return [

            record

            for record

            in self.repository.get_health_records()

            if record.severity
            in [
                "medium",
                "high",
            ]

        ]

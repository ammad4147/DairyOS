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
        return self.repository.save_health(record)

    def record_treatment(
        self,
        treatment,
    ):
        return self.repository.save_treatment(treatment)

    def animals_needing_attention(
        self,
    ):
        """Return observations that require operational/veterinary attention.

        CRITICAL observations must remain visible to the attention workflow.
        This method does not create a treatment or milking prohibition; those
        remain explicit veterinary actions.
        """
        attention_severities = {
            "medium",
            "high",
            "critical",
        }
        return [
            record
            for record in self.repository.get_health_records()
            if str(record.severity or "").strip().lower() in attention_severities
        ]

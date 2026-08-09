class HealthRepository:
    """
    Temporary health event storage.

    Database adapter later.
    """



    def __init__(
        self,
    ):

        self.health_records = []

        self.treatments = []



    def save_health(
        self,
        record,
    ):

        self.health_records.append(
            record
        )

        return record



    def save_treatment(
        self,
        treatment,
    ):

        self.treatments.append(
            treatment
        )

        return treatment



    def get_health_records(
        self,
    ):

        return self.health_records



    def get_treatments(
        self,
    ):

        return self.treatments

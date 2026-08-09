class ReproductionRepository:
    """
    Temporary reproduction storage.
    """



    def __init__(
        self,
    ):

        self.heats = []

        self.inseminations = []

        self.pregnancies = []



    def save_heat(
        self,
        event,
    ):

        self.heats.append(
            event
        )

        return event



    def save_insemination(
        self,
        record,
    ):

        self.inseminations.append(
            record
        )

        return record



    def save_pregnancy(
        self,
        record,
    ):

        self.pregnancies.append(
            record
        )

        return record



    def get_pregnancies(
        self,
    ):

        return self.pregnancies

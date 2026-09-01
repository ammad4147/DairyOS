class ReproductionRepository:
    """
    Temporary reproduction storage.
    """



    def __init__(
        self,
    ):


        self.inseminations = []

        self.pregnancies = []



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

class ReproductionService:



    def __init__(self):

        self.records = []

        self.pregnancies = []



    def add_breeding(

        self,

        record

    ):

        self.records.append(record)

        return record



    def confirm_pregnancy(

        self,

        pregnancy

    ):

        self.pregnancies.append(pregnancy)

        return pregnancy



    def pregnancy_count(self):

        return len(self.pregnancies)

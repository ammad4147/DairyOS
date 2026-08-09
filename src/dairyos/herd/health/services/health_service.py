class HealthService:



    def __init__(self):

        self.records = []

        self.vaccinations = []



    def add_health_record(

        self,

        record

    ):

        self.records.append(record)

        return record



    def add_vaccination(

        self,

        vaccination

    ):

        self.vaccinations.append(vaccination)

        return vaccination



    def health_event_count(self):

        return len(self.records)



    def vaccination_count(self):

        return len(self.vaccinations)

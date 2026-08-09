from ..models.historical_health_record import HistoricalHealthRecord
from ..models.vaccination_history import VaccinationHistory



class HealthHistoryService:



    def __init__(self):

        self.records = []

        self.vaccinations = []



    def add_history_record(

        self,

        record

    ):

        self.records.append(record)

        return record



    def add_vaccination_history(

        self,

        vaccination

    ):

        self.vaccinations.append(vaccination)

        return vaccination



    def get_animal_history(

        self,

        animal_id

    ):

        return [

            record

            for record in self.records

            if record.animal_id == animal_id

        ]



    def get_vaccination_history(

        self,

        animal_id

    ):

        return [

            item

            for item in self.vaccinations

            if item.animal_id == animal_id

        ]

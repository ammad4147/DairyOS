from ..models.animal_record import AnimalRecord



class DatabaseAnimalRepository:



    def __init__(self):

        self.records = {}



    def save(

        self,

        record

    ):


        self.records[

            record.animal_id

        ] = record


        return record



    def find(

        self,

        animal_id

    ):


        return self.records.get(

            animal_id

        )



    def count(self):


        return len(

            self.records

        )

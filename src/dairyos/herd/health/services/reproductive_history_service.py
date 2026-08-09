class ReproductiveHistoryService:



    def __init__(self):

        self.histories = []

        self.inseminations = []



    def add_history(

        self,

        history

    ):

        self.histories.append(history)

        return history



    def add_insemination(

        self,

        record

    ):

        self.inseminations.append(record)

        return record



    def get_animal_history(

        self,

        animal_id

    ):

        return [

            item

            for item in self.histories

            if item.animal_id == animal_id

        ]



    def get_insemination_records(

        self,

        animal_id

    ):

        return [

            item

            for item in self.inseminations

            if item.animal_id == animal_id

        ]

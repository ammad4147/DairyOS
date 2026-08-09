from dairyos.repositories.milk_repository import MilkRepository



class MemoryMilkRepository(MilkRepository):


    def __init__(self):

        self.animals = []

        self.milk_records = []

        self.feed_records = []



    def add_animal(
        self,
        animal
    ):

        self.animals.append(
            animal
        )



    def add_milk(
        self,
        milk
    ):

        self.milk_records.append(
            milk
        )



    def feed_animal(
        self,
        feed
    ):

        self.feed_records.append(
            feed
        )



    def list_animals(
        self
    ):

        return self.animals



    def list_milk(
        self
    ):

        return self.milk_records

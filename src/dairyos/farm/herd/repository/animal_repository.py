from dairyos.farm.herd.models.animal import (
    Animal,
)



class AnimalRepository:
    """
    Temporary in-memory animal storage.

    Later connects to database.
    """


    def __init__(
        self,
    ):

        self.animals = []



    def save(
        self,
        animal: Animal,
    ):

        self.animals.append(
            animal
        )

        return animal



    def get_all(
        self,
    ):

        return self.animals



    def find_by_id(
        self,
        animal_id: str,
    ):

        for animal in self.animals:

            if animal.animal_id == animal_id:

                return animal

        return None

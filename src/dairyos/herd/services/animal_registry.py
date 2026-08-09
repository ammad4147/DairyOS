class AnimalRegistry:


    def __init__(self):

        self.animals = {}



    def register(
        self,
        animal
    ):

        self.animals[
            animal.animal_id
        ] = animal


        return animal



    def get(
        self,
        animal_id
    ):

        return self.animals.get(
            animal_id
        )



    def count(self):

        return len(
            self.animals
        )

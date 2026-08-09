class AnimalRepository:



    def __init__(self):

        self.storage = {}



    def save(

        self,

        animal

    ):


        self.storage[

            animal.animal_id

        ] = animal


        return animal



    def get_by_id(

        self,

        animal_id

    ):


        return self.storage.get(

            animal_id

        )



    def get_all(self):


        return list(

            self.storage.values()

        )



    def delete(

        self,

        animal_id

    ):


        if animal_id in self.storage:

            del self.storage[animal_id]

            return True


        return False

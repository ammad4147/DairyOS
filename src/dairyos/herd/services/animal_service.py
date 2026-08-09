class AnimalService:



    def __init__(

        self,

        repository

    ):

        self.repository = repository



    def register(

        self,

        animal

    ):


        return self.repository.save(

            animal

        )



    def find(

        self,

        animal_id

    ):


        return self.repository.get_by_id(

            animal_id

        )

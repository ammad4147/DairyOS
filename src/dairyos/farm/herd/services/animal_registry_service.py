from dairyos.farm.herd.models.animal import (
    Animal,
)



class AnimalRegistryService:
    """
    Manages dairy animal registration.
    """



    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def register(
        self,
        animal: Animal,
    ):

        return self.repository.save(
            animal
        )



    def herd_count(
        self,
    ):

        return len(
            self.repository.get_all()
        )

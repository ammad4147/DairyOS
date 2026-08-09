from ..models.status import AnimalStatus



class LifecycleService:


    def change_status(
        self,
        animal,
        new_status
    ):

        animal.status = new_status

        return animal

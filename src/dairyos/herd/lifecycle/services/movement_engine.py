from ..models.movement import AnimalMovement



class MovementEngine:


    def __init__(self):

        self.movements = []



    def move(
        self,
        animal,
        new_location,
        reason
    ):

        movement = AnimalMovement(

            animal_id=animal.animal_id,

            from_location=animal.location,

            to_location=new_location,

            reason=reason

        )


        animal.location = new_location


        self.movements.append(
            movement
        )


        return movement

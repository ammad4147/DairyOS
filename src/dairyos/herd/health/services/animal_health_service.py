from ..models.animal_health import AnimalHealth



class AnimalHealthService:



    def evaluate(

        self,

        animal_id,

        condition,

        severity

    ):


        if severity.upper() == "HIGH":

            priority = "HIGH"

            actions = [

                "Veterinary examination",

                "Treatment plan",

                "Monitor milk impact"

            ]



        elif severity.upper() == "MEDIUM":

            priority = "MEDIUM"

            actions = [

                "Review condition",

                "Schedule follow-up"

            ]



        else:

            priority = "NORMAL"

            actions = [

                "Routine monitoring"

            ]



        return AnimalHealth(

            animal_id,

            condition,

            severity,

            priority,

            actions

        )

from ..models.animal_lifecycle import AnimalLifecycle



class AnimalLifecycleService:



    def evaluate(

        self,

        animal_id,

        age_months,

        pregnant=False,

        lactating=False,

        dry=False

    ):


        if age_months < 12:

            stage = "CALF"

            priority = "NORMAL"

            actions = [

                "Monitor growth",

                "Maintain calf nutrition"

            ]



        elif pregnant and age_months >= 22:

            stage = "PREGNANT HEIFER"

            priority = "HIGH"

            actions = [

                "Prepare maternity area",

                "Confirm ration adjustment",

                "Schedule health check"

            ]



        elif lactating:

            stage = "LACTATING COW"

            priority = "HIGH"

            actions = [

                "Monitor milk production",

                "Review health status"

            ]



        elif dry:

            stage = "DRY COW"

            priority = "MEDIUM"

            actions = [

                "Prepare calving plan"

            ]



        else:

            stage = "HEIFER"

            priority = "NORMAL"

            actions = [

                "Monitor development"

            ]



        return AnimalLifecycle(

            animal_id,

            age_months,

            stage,

            priority,

            actions

        )

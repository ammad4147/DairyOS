from ..models.calf_management import CalfManagement



class CalfManagementService:



    def evaluate(

        self,

        animal_id,

        age_months,

        sex

    ):


        if age_months <= 3:

            growth_stage = "PRE-WEANING"

            priority = "HIGH"

            action = "Continue milk and health monitoring"


        elif age_months <= 6:

            growth_stage = "WEANING"

            priority = "MEDIUM"

            action = "Monitor growth development"


        else:

            growth_stage = "GROWING CALF"

            priority = "NORMAL"

            action = "Continue replacement development"



        return CalfManagement(

            animal_id,

            age_months,

            sex,

            growth_stage,

            priority,

            action

        )

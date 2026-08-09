from ..models.replacement_plan import ReplacementPlan



class ReplacementPlanningService:



    def evaluate(

        self,

        current_lactating_cows,

        culling_rate,

        available_heifers

    ):


        required_replacements = int(

            current_lactating_cows * culling_rate

        )



        if available_heifers >= required_replacements:

            status = "SECURE"

            action = "Continue development program"


        else:

            status = "SHORTAGE"

            action = "Increase replacement planning"



        return ReplacementPlan(

            current_lactating_cows,

            culling_rate,

            required_replacements,

            available_heifers,

            status,

            action

        )

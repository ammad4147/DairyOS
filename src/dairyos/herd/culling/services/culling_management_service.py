from ..models.culling_decision import CullingDecision



class CullingManagementService:



    def evaluate(

        self,

        animal_id,

        production_status,

        health_status,

        replacement_available

    ):


        if (

            production_status.lower() == "below target"

            and health_status.lower() == "repeated issues"

            and replacement_available

        ):

            recommendation = "CONSIDER CULLING"

            action = "Veterinary and economic assessment"



        elif health_status.lower() == "repeated issues":

            recommendation = "REVIEW"

            action = "Health intervention required"



        else:

            recommendation = "RETAIN"

            action = "Continue normal management"



        return CullingDecision(

            animal_id,

            production_status,

            health_status,

            replacement_available,

            recommendation,

            action

        )

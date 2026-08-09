from ..models.breeding_management import BreedingManagement



class BreedingManagementService:



    def evaluate(

        self,

        animal_id,

        breeding_event,

        pregnant=False

    ):


        if pregnant:

            pregnancy_status = "PREGNANT"

            priority = "NORMAL"

            next_action = "Prepare calving schedule"



        elif breeding_event.lower() == "ai completed":

            pregnancy_status = "PENDING CONFIRMATION"

            priority = "MEDIUM"

            next_action = "Schedule pregnancy check"



        else:

            pregnancy_status = "NOT BRED"

            priority = "HIGH"

            next_action = "Review breeding plan"



        return BreedingManagement(

            animal_id,

            breeding_event,

            pregnancy_status,

            priority,

            next_action

        )

from ..models.breeding_management import BreedingManagement



class BreedingManagementService:



    def evaluate(

        self,

        animal_id,

        breeding_event,

        pregnant=False

    ):

        # Normalize input for robust matching
        event_normalized = str(breeding_event or "").strip().lower()

        # Synonym map for AI completion events
        ai_synonyms = {
            "ai completed",
            "ai done",
            "artificial insemination",
            "inseminated",
            "ai success",
            "ai performed",
        }



        if pregnant:

            pregnancy_status = "PREGNANT"

            priority = "NORMAL"

            next_action = "Prepare calving schedule"



        elif event_normalized in ai_synonyms:

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

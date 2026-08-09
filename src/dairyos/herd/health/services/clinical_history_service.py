from datetime import datetime

from ..models.clinical_history import ClinicalHistory



class ClinicalHistoryService:


    def record(

        self,

        animal_id,

        complaint,

        previous_conditions,

        previous_treatments,

        reproductive_history,

        feeding_history,

        created_by

    ):

        return ClinicalHistory(

            animal_id=animal_id,

            complaint=complaint,

            previous_conditions=previous_conditions,

            previous_treatments=previous_treatments,

            reproductive_history=reproductive_history,

            feeding_history=feeding_history,

            created_by=created_by,

            created_at=datetime.now()

        )

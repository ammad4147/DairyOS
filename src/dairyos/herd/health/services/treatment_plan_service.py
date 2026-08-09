from datetime import datetime

from ..models.treatment_plan import TreatmentPlan



class TreatmentPlanService:



    def create(

        self,

        animal_id,

        diagnosis,

        treatment,

        dosage_instruction,

        duration,

        responsible_person

    ):

        return TreatmentPlan(

            animal_id=animal_id,

            diagnosis=diagnosis,

            treatment=treatment,

            dosage_instruction=dosage_instruction,

            start_date=datetime.now(),

            duration=duration,

            responsible_person=responsible_person,

            status="ACTIVE"

        )

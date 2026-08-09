from datetime import datetime

from ..models.differential_assessment import DifferentialAssessment



class DifferentialAssessmentService:



    def assess(

        self,

        animal_id,

        possible_condition,

        likelihood,

        supporting_observations,

        veterinarian_notes,

        assessed_by

    ):

        return DifferentialAssessment(

            animal_id=animal_id,

            possible_condition=possible_condition,

            likelihood=likelihood,

            supporting_observations=supporting_observations,

            veterinarian_notes=veterinarian_notes,

            assessed_by=assessed_by,

            assessed_at=datetime.now()

        )

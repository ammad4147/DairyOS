from datetime import datetime

from ..models.clinical_examination import ClinicalExamination
from dairyos.core.time_utils import utcnow


class ClinicalExaminationService:


    def __init__(self):

        self.examinations = []



    def examine(

        self,

        animal_id,

        temperature,

        respiratory_rate,

        heart_rate,

        body_condition_score,

        physical_findings,

        examiner

    ):


        examination = ClinicalExamination(

            animal_id,

            temperature,

            respiratory_rate,

            heart_rate,

            body_condition_score,

            physical_findings,

            examiner,

            utcnow()

        )


        self.examinations.append(

            examination

        )


        return examination



    def record(

        self,

        examination

    ):

        self.examinations.append(

            examination

        )

        return examination



    def get_animal_examinations(

        self,

        animal_id

    ):

        return [

            item

            for item in self.examinations

            if item.animal_id == animal_id

        ]

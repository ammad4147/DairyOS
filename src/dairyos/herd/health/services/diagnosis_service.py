from datetime import datetime

from ..models.diagnosis_record import DiagnosisRecord



class DiagnosisService:



    def record(

        self,

        animal_id,

        diagnosis,

        diagnosis_type,

        confidence,

        diagnosed_by,

        notes=""

    ):

        return DiagnosisRecord(

            animal_id=animal_id,

            diagnosis=diagnosis,

            diagnosis_type=diagnosis_type,

            confidence=confidence,

            diagnosed_by=diagnosed_by,

            notes=notes,

            diagnosed_at=datetime.now()

        )

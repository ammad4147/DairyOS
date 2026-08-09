from datetime import datetime

from ..models.clinical_observation import ClinicalObservation


class ClinicalObservationService:


    def record(

        self,

        animal_id,

        observation_type,

        observation_value,

        severity,

        observed_by,

        notes=""

    ):

        return ClinicalObservation(

            animal_id=animal_id,

            observation_type=observation_type,

            observation_value=observation_value,

            severity=severity,

            observed_by=observed_by,

            observed_at=datetime.now(),

            notes=notes

        )

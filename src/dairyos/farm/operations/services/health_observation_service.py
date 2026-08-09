from dairyos.farm.operations.models.health_observation import (
    HealthObservation,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class HealthObservationService:
    """
    Processes animal health observations
    entered by farm personnel.
    """


    def record(
        self,
        observation: HealthObservation,
    ):

        return FarmOperationEvent(

            event_type="health_observation_recorded",

            animal_id=observation.animal_id,

            operator=observation.operator,

            payload={

                "observation":
                    observation.observation_type,

                "notes":
                    observation.notes,

                "severity":
                    getattr(
                        observation,
                        "severity",
                        "normal",
                    ),

            },

        )

from dairyos.farm.operations.repositories.health_repository import (
    HealthRepository,
)

from dairyos.data.models import (
    HealthObservation as DatabaseHealthObservation,
)


class DatabaseHealthRepository(
    HealthRepository,
):
    """
    PostgreSQL-backed health observation repository adapter.
    """


    def __init__(
        self,
        session,
    ):

        self.session = session



    def save(
        self,
        observation,
    ):

        health = DatabaseHealthObservation(

            animal_id=(
                observation.animal_id
            ),

            observed_at=(
                observation.timestamp.replace(
                    tzinfo=None
                )
            ),

            notes=(
                observation.observation
            ),

            severity=(
                observation.severity
            ),

            observer=(
                observation.reported_by
            ),

            temperature_c=(
                observation.temperature
            ),

        )


        self.session.add(
            health
        )

        self.session.commit()

        self.session.refresh(
            health
        )


        return observation



    def get_all(
        self,
    ):

        return (
            self.session.query(
                DatabaseHealthObservation
            )
            .all()
        )

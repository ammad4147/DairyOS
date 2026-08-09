from dairyos.farm.operations.repositories.milk_repository import (
    MilkRepository,
)

from dairyos.data.models import (
    MilkProduction,
)


class DatabaseMilkRepository(
    MilkRepository,
):
    """
    PostgreSQL-backed milk repository adapter.

    Converts FarmOperations domain MilkRecord objects
    into SQLAlchemy MilkProduction records.
    """


    def __init__(
        self,
        session,
    ):

        self.session = session



    def save(
        self,
        record,
    ):

        production = MilkProduction(

            animal_id=(
                record.animal_id
                if record.animal_id is not None
                else record.animal_group
            ),

            production_date=(
                record.timestamp.replace(
                    tzinfo=None
                )
            ),

        )


        shift = (
            record.shift.upper()
        )


        if shift == "MORNING":

            production.morning_yield = (
                record.litres
            )


        elif shift == "AFTERNOON":

            production.afternoon_yield = (
                record.litres
            )


        elif shift == "EVENING":

            production.evening_yield = (
                record.litres
            )


        else:

            production.morning_yield = (
                record.litres
            )


        production.calculate_total()


        self.session.add(
            production
        )

        self.session.commit()

        self.session.refresh(
            production
        )


        return record



    def get_all(
        self,
    ):

        return (
            self.session.query(
                MilkProduction
            )
            .all()
        )

from dairyos.data.repositories.repository_factory import RepositoryFactory

from ..models.milk_production import MilkProduction


class MilkProductionService:


    def __init__(self, session=None):

        self.session = session

        self.records = []

        self.repository = None

        if session is not None:

            self.repository = (
                RepositoryFactory(session)
                .milk_production_repository()
            )


    def record(self, production):

        if self.repository:

            self.repository.add(production)

        else:

            self.records.append(production)

        return production


    def record_count(self):

        if self.repository:

            return self.repository.count()

        return len(self.records)


    def evaluate(

        self,

        animal_group,

        animal_count,

        expected_milk,

        actual_milk

    ):

        variance = actual_milk - expected_milk

        if actual_milk >= expected_milk:

            status = "ON TARGET"

        else:

            status = "ATTENTION"

        return MilkProduction(

            animal_group,

            animal_count,

            expected_milk,

            actual_milk,

            variance,

            status

        )

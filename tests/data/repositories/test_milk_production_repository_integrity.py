from types import SimpleNamespace

import pytest

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.repositories.milk_production_repository import MilkProductionRepository


class FakeAnimalRepository:
    def __init__(self, animal):
        self.animal = animal

    def get_by_animal_id(self, animal_id):
        if self.animal and self.animal.animal_id == str(animal_id):
            return self.animal
        return None

    def exists(self, animal_id):
        return self.get_by_animal_id(animal_id) is not None


def _animal(*, active=True, lifecycle_status="LACTATING"):
    return SimpleNamespace(
        animal_id="TD-INTEGRITY-01",
        active=active,
        lifecycle_status=lifecycle_status,
    )


def test_repository_rejects_negative_milk_yield():
    repository = MilkProductionRepository(
        animal_repository=FakeAnimalRepository(_animal())
    )
    production = MilkProduction(
        animal_id="TD-INTEGRITY-01",
        milking_session="MORNING",
        morning_yield=-1.0,
    )

    with pytest.raises(ValueError, match="morning_yield"):
        repository.add(production)


def test_repository_rejects_inactive_animal():
    repository = MilkProductionRepository(
        animal_repository=FakeAnimalRepository(
            _animal(active=False, lifecycle_status="DECEASED")
        )
    )
    production = MilkProduction(
        animal_id="TD-INTEGRITY-01",
        milking_session="MORNING",
        morning_yield=10.0,
    )

    with pytest.raises(ValueError, match="DECEASED"):
        repository.add(production)


def test_repository_accepts_valid_active_animal_and_nonnegative_yield():
    repository = MilkProductionRepository(
        animal_repository=FakeAnimalRepository(_animal())
    )
    production = MilkProduction(
        animal_id="TD-INTEGRITY-01",
        milking_session="MORNING",
        morning_yield=10.0,
    )

    saved = repository.add(production)

    assert saved is production
    assert repository.count() == 1

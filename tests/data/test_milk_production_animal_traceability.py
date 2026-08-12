import pytest

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.repositories.milk_production_repository import MilkProductionRepository


class _AnimalRepository:
    def __init__(self, animal_ids):
        self.animal_ids = set(animal_ids)

    def exists(self, animal_id):
        return animal_id in self.animal_ids


def _production(animal_id):
    return MilkProduction(
        animal_id=animal_id,
        morning_yield=10.0,
        afternoon_yield=5.0,
        evening_yield=5.0,
        total_yield=20.0,
    )


def test_milk_persistence_requires_existing_permanent_animal_id():
    repository = MilkProductionRepository(
        animal_repository=_AnimalRepository({"AN-0001"})
    )

    with pytest.raises(ValueError, match="does not exist"):
        repository.save(_production("AN-MISSING"))

    assert repository.get_all() == []


def test_milk_persistence_accepts_existing_permanent_animal_id():
    repository = MilkProductionRepository(
        animal_repository=_AnimalRepository({"AN-0001"})
    )

    record = repository.save(_production("AN-0001"))

    assert record.animal_id == "AN-0001"
    assert repository.get_by_animal_id("AN-0001") == [record]

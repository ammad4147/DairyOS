from types import SimpleNamespace

from dairyos.farm.production.models.non_milking_directive import (
    NonMilkingDirective,
)
from dairyos.farm.production.services.non_milking_directive_service import (
    NonMilkingDirectiveService,
)


class FakeAnimalRepository:
    def __init__(self):
        self.animals = {
            "TD-001": SimpleNamespace(
                animal_id="TD-001",
                lifecycle_status="LACTATING",
                is_currently_milking=True,
                non_milking_directive="NONE",
                non_milking_since=None,
                non_milking_until=None,
                non_milking_reason=None,
                non_milking_changed_by=None,
                non_milking_restore_to_milking=False,
            )
        }

    def get_by_animal_id(self, animal_id):
        return self.animals.get(str(animal_id))

    def save(self, animal):
        self.animals[animal.animal_id] = animal
        return animal


class FakeFindingService:
    def __init__(self):
        self.raised = []
        self.resolved = []

    class Repository:
        def find_open_by_dedupe_key(self, key):
            return None

    @property
    def repository(self):
        return self.Repository()

    def raise_or_update(self, **kwargs):
        self.raised.append(kwargs)
        return SimpleNamespace(
            finding_id="HL-260817-001"
        )

    def resolve(self, *args, **kwargs):
        self.resolved.append(
            (args, kwargs)
        )
        return SimpleNamespace(
            finding_id="HL-260817-001"
        )


def test_temporary_non_milking_moves_animal_to_dry_and_out_of_milking():
    repository = FakeAnimalRepository()
    findings = FakeFindingService()

    service = NonMilkingDirectiveService(
        repository,
        finding_service=findings,
    )

    animal = service.apply(
        "TD-001",
        NonMilkingDirective.TEMPORARY_NON_MILKING,
        reason="Clinical recovery",
        changed_by="Vet",
    )

    assert animal.non_milking_directive == (
        NonMilkingDirective.TEMPORARY_NON_MILKING.value
    )
    assert animal.lifecycle_status == "DRY"
    assert animal.is_currently_milking is False
    assert findings.raised


def test_milk_separately_is_outside_active_herd_but_expects_milk():
    repository = FakeAnimalRepository()
    findings = FakeFindingService()

    service = NonMilkingDirectiveService(
        repository,
        finding_service=findings,
    )

    animal = service.apply(
        "TD-001",
        NonMilkingDirective.MILK_SEPARATELY,
        reason="Milk to be separated",
        changed_by="Vet",
    )

    assert animal.non_milking_directive == (
        NonMilkingDirective.MILK_SEPARATELY.value
    )
    assert animal.is_currently_milking is False
    assert animal.lifecycle_status == "DRY"
    assert service.expects_milk(animal) is True
    assert service.is_outside_active_milking_herd(animal) is True


def test_permanent_non_milking_is_zero_expected_milk():
    repository = FakeAnimalRepository()

    service = NonMilkingDirectiveService(
        repository
    )

    animal = service.apply(
        "TD-001",
        NonMilkingDirective.PERMANENT_NON_MILKING,
        reason="Permanent veterinary instruction",
        changed_by="Vet",
    )

    assert animal.lifecycle_status == "DRY"
    assert animal.is_currently_milking is False
    assert service.expects_milk(animal) is False


def test_clear_restores_previous_milking_state():
    repository = FakeAnimalRepository()

    service = NonMilkingDirectiveService(
        repository
    )

    service.apply(
        "TD-001",
        NonMilkingDirective.TEMPORARY_NON_MILKING,
        reason="Recovery",
        changed_by="Vet",
    )

    animal = service.clear(
        "TD-001",
        changed_by="Vet",
        reason="Healthy - return to milking",
    )

    assert animal.non_milking_directive == "NONE"
    assert animal.is_currently_milking is True
    assert animal.lifecycle_status == "LACTATING"
    assert animal.non_milking_since is None
    assert animal.non_milking_until is None


def test_schedule_service_excludes_zero_expected_directive():
    from dairyos.farm.herd.services.animal_milking_schedule_service import (
        AnimalMilkingScheduleService,
    )

    animal = SimpleNamespace(
        animal_id="TD-001",
        milking_frequency="THRICE_DAILY",
        non_milking_directive=(
            NonMilkingDirective.TEMPORARY_NON_MILKING.value
        ),
    )

    service = AnimalMilkingScheduleService()

    assert service.get_expected_sessions(
        animal,
        "2026-08-17",
    ) == []


def test_schedule_service_keeps_milk_separately_as_expected_milk():
    from dairyos.farm.herd.services.animal_milking_schedule_service import (
        AnimalMilkingScheduleService,
    )

    animal = SimpleNamespace(
        animal_id="TD-001",
        milking_frequency="THRICE_DAILY",
        non_milking_directive=(
            NonMilkingDirective.MILK_SEPARATELY.value
        ),
    )

    service = AnimalMilkingScheduleService()

    assert service.get_expected_sessions(
        animal,
        "2026-08-17",
    ) == [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ]

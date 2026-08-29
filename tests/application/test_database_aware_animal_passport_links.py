from datetime import date, datetime
from types import SimpleNamespace

from dairyos.application.database_aware_animal_passport import (
    DatabaseAwareLifetimeAnimalPassportService,
)


class _HistoryRepo:
    def __init__(self, records):
        self.records = records

    def get_by_animal_id(self, animal_id):
        return [
            record
            for record in self.records
            if str(getattr(record, "animal_id", "")) == animal_id
        ]

    def get_by_animal(self, animal_id):
        return self.get_by_animal_id(animal_id)

    def get_all(self):
        return list(self.records)


class _AnimalRepo(_HistoryRepo):
    def get_by_animal_id(self, animal_id):
        return next(
            (
                record
                for record in self.records
                if str(getattr(record, "animal_id", "")) == animal_id
            ),
            None,
        )


class _Factory:
    def __init__(self, animal, milk, health, cases, treatments, breeding, feed, finance, events):
        self._repos = {
            "animal": _AnimalRepo([animal]),
            "milk": _HistoryRepo(milk),
            "health": _HistoryRepo(health),
            "health_cases": _HistoryRepo(cases),
            "treatment": _HistoryRepo(treatments),
            "breeding": _HistoryRepo(breeding),
            "feed": _HistoryRepo(feed),
            "finance": _HistoryRepo(finance),
            "operational_events": _HistoryRepo(events),
        }

    def __getattr__(self, name):
        repository = self._repos.get(name)
        if repository is None:
            raise AttributeError(name)
        return lambda: repository


def _animal(animal_id="AN-001"):
    return SimpleNamespace(
        id=1,
        animal_id=animal_id,
        animal_type="CATTLE",
        ear_tag="001",
        rfid="RF-001",
        breed="HF",
        sex="FEMALE",
        date_of_birth=date(2023, 1, 1),
        dam_id=None,
        sire_id=None,
        lifecycle_status="LACTATING",
        status="ACTIVE",
        is_currently_milking=True,
        milking_frequency="TWICE_DAILY",
        production_group="MILKING",
        location="Shed A",
        active=True,
        non_milking_directive="NONE",
        non_milking_reason=None,
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2026, 8, 29),
    )


def test_passport_build_links_all_animal_scoped_sources():
    animal = _animal()
    milk = [SimpleNamespace(animal_id="AN-001", production_date=date(2026, 8, 29), total_yield=24.0)]
    health = [SimpleNamespace(animal_id="AN-001", observation_date=date(2026, 8, 29), observation="Normal")]
    cases = []
    treatments = []
    breeding = []
    feed = [SimpleNamespace(animal_id="AN-001", feeding_date=date(2026, 8, 29), quantity=10)]
    finance = [SimpleNamespace(animal_id="AN-001", transaction_date=date(2026, 8, 29), amount=1000)]
    events = [SimpleNamespace(animal_id="AN-001", event_date=date(2026, 8, 29), description="animal_id=AN-001")]

    factory = _Factory(animal, milk, health, cases, treatments, breeding, feed, finance, events)
    passport = DatabaseAwareLifetimeAnimalPassportService(factory).build("AN-001")

    assert passport is not None
    assert passport["animal"]["animal_id"] == "AN-001"
    assert passport["history"]["milk"]
    assert passport["history"]["health"]
    assert passport["history"]["feed"]
    assert passport["history"]["finance"]
    assert passport["history"]["operational_events"]
    assert passport["record_counts"]["milk"] == 1
    assert passport["record_counts"]["health"] == 1
    assert passport["record_counts"]["feed"] == 1
    assert passport["record_counts"]["finance"] == 1


def test_passport_rejects_unknown_animal_id_without_partial_projection():
    animal = _animal()
    animal.rfid = None
    animal.date_of_birth = None
    animal.production_group = None
    animal.location = None
    factory = _Factory(animal, [], [], [], [], [], [], [], [])

    assert DatabaseAwareLifetimeAnimalPassportService(factory).build("MISSING") is None

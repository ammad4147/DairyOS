from datetime import date, datetime, timezone
from types import SimpleNamespace

from dairyos.application.database_aware_animal_passport import (
    DatabaseAwareLifetimeAnimalPassportService,
)


class _AnimalRepo:
    def __init__(self, animal):
        self.animal = animal

    def get_by_animal_id(self, animal_id):
        return self.animal if self.animal.animal_id == animal_id else None

    def get_all(self):
        return [self.animal]

    def get_milking_frequency_history(self, animal_id):
        return []


class _HistoryRepo:
    def get_all(self):
        return []

    def get_by_animal(self, animal_id):
        return []

    def get_by_animal_id(self, animal_id):
        return []


class _Session:
    def __init__(self, payload):
        self.payload = payload

    def query(self, model):
        return self

    def filter(self, criterion):
        return self

    def first(self):
        return SimpleNamespace(farm_id="DEFAULT", state_payload=self.payload)


class _Factory:
    def __init__(self, animal, welfare):
        self.session = _Session({"animal_welfare_observations": welfare})
        self._animal = _AnimalRepo(animal)
        self._repos = {name: _HistoryRepo() for name in (
            "milk", "health", "health_cases", "treatment",
            "breeding", "feed", "finance", "operational_events",
        )}

    def animal(self):
        return self._animal

    def __getattr__(self, name):
        repository = self._repos.get(name)
        if repository is None:
            raise AttributeError(name)
        return lambda: repository


def _animal():
    return SimpleNamespace(
        id=1,
        animal_id="AN-001",
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
        updated_at=datetime(2026, 8, 30),
    )


def test_passport_links_persisted_welfare_and_honors_historical_date():
    welfare = [
        {
            "animal_id": "AN-001",
            "welfare_domain": "GENERAL",
            "score": 82,
            "status": "OBSERVED",
            "observed_at": datetime(2026, 8, 29, tzinfo=timezone.utc).isoformat(),
        },
        {
            "animal_id": "AN-001",
            "welfare_domain": "GENERAL",
            "score": 91,
            "status": "OBSERVED",
            "observed_at": datetime(2026, 8, 30, tzinfo=timezone.utc).isoformat(),
        },
    ]
    passport = DatabaseAwareLifetimeAnimalPassportService(
        _Factory(_animal(), welfare)
    ).build("AN-001", as_of_date=date(2026, 8, 29))

    linked = passport["health_state"]["welfare"]
    assert linked["data_status"] == "LIVE_PERSISTED_DATA"
    assert linked["observation_count"] == 1
    assert linked["latest"]["score"] == 82

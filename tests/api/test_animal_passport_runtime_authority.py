from datetime import date, datetime
from types import SimpleNamespace

import dairyos.api.animal_operational_records as operational_records_api
from dairyos.api.animal_passport import get_lifetime_passport, get_reproductive_state


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


class _Factory:
    def __init__(self, animal):
        self.calls = []
        self._repos = {
            "animal": _AnimalRepo(animal),
            "milk": _HistoryRepo([
                SimpleNamespace(
                    animal_id=animal.animal_id,
                    production_date=date(2026, 8, 30),
                    total_yield=24.0,
                )
            ]),
            "health": _HistoryRepo([
                SimpleNamespace(
                    animal_id=animal.animal_id,
                    observation_date=date(2026, 8, 30),
                    observation="Normal",
                )
            ]),
            "health_cases": _HistoryRepo([]),
            "treatment": _HistoryRepo([]),
            "breeding": _HistoryRepo([]),
            "feed": _HistoryRepo([
                SimpleNamespace(
                    animal_id=animal.animal_id,
                    feeding_date=date(2026, 8, 30),
                    quantity=10,
                )
            ]),
            "finance": _HistoryRepo([
                SimpleNamespace(
                    animal_id=animal.animal_id,
                    transaction_date=date(2026, 8, 30),
                    amount=1000,
                )
            ]),
            "operational_events": _HistoryRepo([
                SimpleNamespace(
                    animal_id=animal.animal_id,
                    event_date=date(2026, 8, 30),
                    description=f"animal_id={animal.animal_id}",
                )
            ]),
        }

    def __getattr__(self, name):
        repository = self._repos.get(name)
        if repository is None:
            raise AttributeError(name)
        self.calls.append(name)
        return lambda: repository


class _Container:
    def __init__(self, factory):
        self.repository_factory = factory


class _Runtime:
    def __init__(self, factory):
        self.repository_factory = factory
        self.animal_repository = factory.animal()


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


def test_passport_uses_canonical_runtime_repository_factory():
    factory = _Factory(_animal())
    container = _Container(factory)

    passport = get_lifetime_passport("AN-001", container=container)

    assert passport is not None
    assert passport["animal"]["animal_id"] == "AN-001"
    assert passport["history"]["milk"]
    assert passport["history"]["health"]
    assert passport["history"]["feed"]
    assert passport["history"]["finance"]
    assert passport["history"]["operational_events"]
    assert "animal" in factory.calls
    assert "milk" in factory.calls
    assert "health" in factory.calls
    assert "feed" in factory.calls
    assert "finance" in factory.calls


def test_reproductive_state_uses_same_runtime_factory():
    factory = _Factory(_animal())
    container = _Container(factory)

    payload = get_reproductive_state("AN-001", container=container)

    assert payload["animal_id"] == "AN-001"
    assert "breeding" in factory.calls


def test_operational_record_endpoints_use_canonical_factory(monkeypatch):
    animal = _animal()
    factory = _Factory(animal)
    runtime = _Runtime(factory)
    monkeypatch.setattr(operational_records_api, "_runtime", lambda: runtime)

    payload = operational_records_api.animal_operational_records("AN-001")

    assert payload["animal_id"] == "AN-001"
    assert len(payload["milk"]) == 1
    assert len(payload["feed"]) == 1
    assert len(payload["health"]) == 1
    assert len(payload["finance"]) == 1
    assert payload["source"] == "authoritative_persistence"

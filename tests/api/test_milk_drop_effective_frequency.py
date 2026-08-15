from datetime import date
from types import SimpleNamespace

from dairyos.api.farm_data_entry import _detect_and_raise_milk_drop


def test_drop_detection_resolves_frequency_for_operational_date(
    monkeypatch,
):
    animal = SimpleNamespace(
        animal_id="TEST-MILK-FREQ-001",
        milking_frequency="TWICE_DAILY",
    )

    class FakeAnimalRepository:
        def get_by_animal_id(self, animal_id):
            return animal

        def get_milking_frequency_history(self, animal_id):
            return [
                SimpleNamespace(
                    milking_frequency="THRICE_DAILY",
                    effective_from="2026-08-15T00:00:00",
                    effective_to="2026-08-16T00:00:00",
                ),
                SimpleNamespace(
                    milking_frequency="TWICE_DAILY",
                    effective_from="2026-08-16T00:00:00",
                    effective_to=None,
                ),
            ]

    class FakeFactory:
        def animal(self):
            return FakeAnimalRepository()

        def operational_findings(self):
            return None

    captured = {}

    def fake_detect_drop(*args, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(
        "dairyos.api.farm_data_entry.detect_drop",
        fake_detect_drop,
    )

    monkeypatch.setattr(
        "dairyos.api.farm_data_entry._list_by_type",
        lambda *args, **kwargs: [],
    )

    _detect_and_raise_milk_drop(
        FakeFactory(),
        animal_id="TEST-MILK-FREQ-001",
        session="AFTERNOON",
        as_of_date=date(2026, 8, 15),
    )

    assert captured["milking_frequency"] == "THRICE_DAILY"
    assert captured["as_of_date"] == date(2026, 8, 15)


def test_drop_detection_does_not_use_current_frequency_for_historical_date(
    monkeypatch,
):
    animal = SimpleNamespace(
        animal_id="TEST-MILK-FREQ-002",
        milking_frequency="TWICE_DAILY",
    )

    class FakeAnimalRepository:
        def get_by_animal_id(self, animal_id):
            return animal

        def get_milking_frequency_history(self, animal_id):
            return [
                SimpleNamespace(
                    milking_frequency="THRICE_DAILY",
                    effective_from="2026-08-15T00:00:00",
                    effective_to="2026-08-16T00:00:00",
                ),
            ]

    class FakeFactory:
        def animal(self):
            return FakeAnimalRepository()

        def operational_findings(self):
            return None

    captured = {}

    def fake_detect_drop(*args, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(
        "dairyos.api.farm_data_entry.detect_drop",
        fake_detect_drop,
    )

    monkeypatch.setattr(
        "dairyos.api.farm_data_entry._list_by_type",
        lambda *args, **kwargs: [],
    )

    _detect_and_raise_milk_drop(
        FakeFactory(),
        animal_id="TEST-MILK-FREQ-002",
        session="AFTERNOON",
        as_of_date=date(2026, 8, 15),
    )

    assert captured["milking_frequency"] != animal.milking_frequency
    assert captured["milking_frequency"] == "THRICE_DAILY"

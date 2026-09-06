from pathlib import Path
from types import SimpleNamespace

from dairyos.api.search import animal_document


ROOT = Path(__file__).resolve().parents[2]

SEARCH = (
    ROOT / "src/dairyos/api/search.py"
).read_text(encoding="utf-8")

INDEXER = (
    ROOT / "src/dairyos/api/index_animals.py"
).read_text(encoding="utf-8")


def test_search_projection_uses_authoritative_animal_fields():
    animal = SimpleNamespace(
        animal_id="DO-0001",
        legacy_animal_id="OLD-17",
        ear_tag="PK-100",
        rfid="RF-22",
        animal_type="MILKING",
        breed="Holstein",
        sex="FEMALE",
        status="ACTIVE",
        lifecycle_status="ACTIVE",
        active=True,
        production_group="HIGH",
        location="Shed A",
        date_of_birth=None,
    )

    doc = animal_document(animal)

    assert doc["animal_id"] == "DO-0001"
    assert doc["legacy_animal_id"] == "OLD-17"
    assert doc["ear_tag"] == "PK-100"
    assert doc["rfid"] == "RF-22"
    assert doc["active"] is True


def test_indexer_uses_dairyos_repository_not_database_credentials():
    assert "RepositoryFactory.create()" in INDEXER
    assert "factory.animal().get_all()" in INDEXER

    assert "postgresql://" not in INDEXER
    assert "create_engine" not in INDEXER
    assert "herd.animals" not in INDEXER
    assert "LIMIT 1000" not in INDEXER


def test_elasticsearch_is_optional_and_not_connected_during_import():
    assert "def create_search_client()" in SEARCH

    prefix = SEARCH.split(
        "def create_search_client()",
        1,
    )[0]

    assert ".info()" not in prefix
    assert ".ping()" not in prefix


def test_search_projection_preserves_inactive_animals():
    assert "factory.animal().get_all()" in INDEXER
    assert "active_animals()" not in INDEXER


def test_normal_indexing_does_not_delete_search_index():
    assert "if rebuild and client.indices.exists" in INDEXER
    assert "--rebuild" in INDEXER
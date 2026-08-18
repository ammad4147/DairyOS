from fastapi.testclient import TestClient


def test_animals_tab_reads_canonical_persisted_animal_register(
    client: TestClient,
    registered_animal: str,
):
    response = client.get(
        "/operations/tab-state"
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    animals_tab = payload["tabs"]["animals"]

    assert animals_tab["status"] == "ACTIVE"
    assert animals_tab["source"] == "FarmOperationalState"
    assert (
        animals_tab["source_detail"]
        == "Canonical Animal Register"
    )

    animals = animals_tab["state"]["animals"]

    assert registered_animal in animals

    animal = animals[registered_animal]

    assert animal["animal_id"] == registered_animal
    assert animal["lifecycle_status"] == "LACTATING"
    assert animal["status"] == "MILKING"
    assert animal["is_currently_milking"] is True
    assert animal["milking_frequency"] == "THRICE_DAILY"
    assert animal["active"] is True


def test_single_animals_tab_reads_canonical_persisted_animal_register(
    client: TestClient,
    registered_animal: str,
):
    response = client.get(
        "/operations/tab-state/animals"
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["tab_id"] == "animals"
    assert payload["status"] == "ACTIVE"

    animals = payload["state"]["animals"]

    assert registered_animal in animals

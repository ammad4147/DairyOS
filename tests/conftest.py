import pytest
from fastapi.testclient import TestClient

from dairyos.app import app, container

from dairyos.runtime.persistent_event_journal import PersistentEventJournal

from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)

from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)



@pytest.fixture()
def client(tmp_path):

    journal = PersistentEventJournal()

    journal.clear()


    container.event_journal = journal


    #
    # Preserve production dependency wiring.
    #
    container.animal_operational_state_repository = (
        AnimalOperationalStateRepository(storage_path=tmp_path / "animal_operational_states.json")
    )


    container.animal_event_projection = (
        AnimalEventProjection(
            repository=(
                container.animal_operational_state_repository
            )
        )
    )


    container.farm_operational_state_service = (
        FarmOperationalStateService(
            animal_projection=(
                container.animal_event_projection
            )
        )
    )


    container.started = False

    container.operations = None

    container.dashboard = None


    print(
        "FIXTURE RESET:",
        container.event_journal.count(),
        flush=True
    )


    with TestClient(app) as c:

        print(
            "AFTER STARTUP:",
            container.event_journal.count(),
            flush=True
        )

        yield c

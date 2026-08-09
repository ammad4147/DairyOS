from datetime import datetime, timezone

from dairyos.data.database.session import SessionLocal

from dairyos.data.repositories.repository_factory import (
    RepositoryFactory,
)

from dairyos.farm.operations.models.breeding_record import (
    BreedingRecord,
)


def test_repository_factory_exposes_breeding_repository():

    session = SessionLocal()

    try:
        factory = RepositoryFactory.create(
            session=session,
        )

        repository = factory.breeding()

        assert repository is not None

    finally:
        session.close()



def test_breeding_repository_can_persist_event():

    session = SessionLocal()

    try:
        factory = RepositoryFactory.create(
            session=session,
        )

        repository = factory.breeding()

        record = BreedingRecord(
            animal_id="TEST-ANIMAL-001",
            event_type="insemination",
            result="pending",
            technician="Sprint-039-Test",
        )

        saved = repository.save(
            record
        )

        session.commit()

        assert saved is not None
        assert saved.animal_id == "TEST-ANIMAL-001"

    finally:
        session.rollback()
        session.close()



def test_breeding_repository_query_boundary_exists():

    session = SessionLocal()

    try:
        factory = RepositoryFactory.create(
            session=session,
        )

        repository = factory.breeding()

        assert hasattr(
            repository,
            "save",
        )

        assert hasattr(
            repository,
            "get_all",
        )

    finally:
        session.close()
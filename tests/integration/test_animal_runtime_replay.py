from datetime import datetime, UTC


from dairyos.app import container
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.database.session import SessionLocal

from dairyos.domain.events import Event


def test_runtime_restore_rebuilds_animal_operational_state():

    session = SessionLocal()
    try:
        for row in session.query(EventJournalModel).all():
            session.delete(row)
            session.flush()
        session.commit()
    finally:
        session.close()


    event = Event(
        name="lifecycle_changed",
        payload={
            "animal_id": "COW-RUNTIME-001",

            "previous_status": "HEIFER",

            "new_status": "LACTATING",

            "location": "MILKING_SHED",

            "operator": "farm_manager",

            "timestamp": (
                datetime.now(UTC)
                .isoformat()
            ),
        },
    )


    container.event_journal.append(
        event
    )


    #
    # Simulate projection restart.
    #
    container.animal_operational_state_repository = (
        type(
            container.animal_operational_state_repository
        )()
    )


    container.animal_event_projection.repository = (
        container.animal_operational_state_repository
    )


    container.restore_state()


    restored = (
        container.animal_operational_state_repository.get(
            "COW-RUNTIME-001"
        )
    )


    assert restored is not None

    assert restored.animal_id == (
        "COW-RUNTIME-001"
    )

    assert restored.lifecycle_status == (
        "LACTATING"
    )

    assert restored.animal_status == (
        "LACTATING"
    )

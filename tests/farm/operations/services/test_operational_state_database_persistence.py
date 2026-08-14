from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dairyos.data.database.base import Base

from dairyos.data.repositories.database_operational_state_repository import (
    DatabaseOperationalStateRepository,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)



def test_database_operational_state_persistence():

    engine = create_engine(
        "sqlite:///:memory:"
    )


    Base.metadata.create_all(
        bind=engine
    )


    Session = sessionmaker(
        bind=engine
    )


    session_one = Session()


    repository_one = DatabaseOperationalStateRepository(
        session=session_one
    )


    service_one = FarmOperationalStateService(
        repository=repository_one
    )


    event = FarmOperationEvent(

        event_type="milk_recorded",

        animal_id=None,

        operator="Farm Manager",

        payload={
            "shift": "morning",
            "litres": 620,
        },

    )


    service_one.process_event(
        event
    )


    session_one.close()



    session_two = Session()


    repository_two = DatabaseOperationalStateRepository(
        session=session_two
    )


    service_two = FarmOperationalStateService(
        repository=repository_two
    )


    state = service_two.get_state()


    assert (
        state.milk_status["morning"]["litres"]
        ==
        620
    )


    session_two.close()

    engine.dispose()

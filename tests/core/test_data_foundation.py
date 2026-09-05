from dairyos.data.database.database import initialize_database
from dairyos.data.database.session import SessionLocal, engine
from dairyos.data.database.models.farm_model import FarmModel
from dairyos.data.models.farm import Farm
from dairyos.data.models.animal import Animal
from dairyos.data.repositories.farm_repository import FarmRepository
from dairyos.data.repositories.animal_repository import AnimalRepository


def _clean_farms(session):
    for row in session.query(FarmModel).all():
        session.delete(row)
        session.flush()
    session.commit()


def test_database_engine_connection():
    connection = engine.connect()

    try:
        assert connection is not None
    finally:
        connection.close()


def test_database_engine_is_canonical():
    assert engine is not None
    assert SessionLocal is not None


def test_farm_creation():
    farm = Farm(
        "F001",
        "Trident Dairies",
        "Lahore",
    )

    assert farm.farm_name == "Trident Dairies"


def test_animal_creation():
    animal = Animal(
        "A001",
        "Holstein",
        "ACTIVE",
    )

    assert animal.status == "ACTIVE"


def test_farm_repository():
    initialize_database()

    session = SessionLocal()

    try:
        _clean_farms(session)

        repo = FarmRepository(session)

        repo.add(
            Farm(
                "F001",
                "Trident Dairies",
                "Lahore",
            )
        )

        assert repo.count() == 1

    finally:
        _clean_farms(session)
        session.close()


def test_animal_repository():
    repo = AnimalRepository()

    repo.add(
        Animal(
            "A001",
            "Holstein",
            "ACTIVE",
        )
    )

    assert repo.count() == 1


def test_multiple_animals():
    repo = AnimalRepository()

    repo.add(
        Animal(
            "A001",
            "Cow",
            "ACTIVE",
        )
    )

    repo.add(
        Animal(
            "A002",
            "Cow",
            "ACTIVE",
        )
    )

    assert repo.count() == 2


def test_multiple_farms():
    initialize_database()

    session = SessionLocal()

    try:
        _clean_farms(session)

        repo = FarmRepository(session)

        repo.add(
            Farm(
                "F001",
                "Farm One",
                "Lahore",
            )
        )

        repo.add(
            Farm(
                "F002",
                "Farm Two",
                "Punjab",
            )
        )

        assert repo.count() == 2

    finally:
        _clean_farms(session)
        session.close()


def test_data_layer_exists():
    assert engine is not None
    assert SessionLocal is not None


def test_foundation_complete():
    assert FarmRepository is not None

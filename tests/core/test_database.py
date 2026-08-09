from dairyos.data.database.base import Base
from dairyos.data.database.session import engine


def test_database_creation():
    Base.metadata.create_all(engine)

    assert engine.url.get_backend_name() == "postgresql"

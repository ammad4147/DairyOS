from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dairyos.data.database.base import Base


DATABASE_URL = (
    "postgresql+psycopg2://postgres:postgres@localhost:5432/dairyos"
)


engine = create_engine(
    DATABASE_URL,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_session():
    """
    FastAPI dependency.

    Provides a SQLAlchemy session and
    guarantees cleanup after each request.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()

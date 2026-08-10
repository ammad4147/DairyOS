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
    FastAPI request-scoped database dependency.

    A new SQLAlchemy Session is created for the request and is
    always closed when the dependency lifecycle ends.

    Application-level components that need a long-lived session
    must use SessionLocal() directly through their composition
    boundary rather than consuming this generator.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def create_application_session():
    """
    Create an application-owned SQLAlchemy session.

    The caller owns the lifecycle and must eventually call
    session.close().

    This function exists so application composition does not
    misuse the FastAPI dependency generator.
    """

    return SessionLocal()

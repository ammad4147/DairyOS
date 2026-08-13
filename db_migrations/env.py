from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from dairyos.data.database.session import Base, DATABASE_URL

# ---------------------------------------------------------------------------
# AUTHORITATIVE ORM MODEL REGISTRATION
# ---------------------------------------------------------------------------
#
# DairyOS uses the authoritative ORM model boundary under
# dairyos.data.models.
#
# Legacy duplicate ORM models are intentionally NOT imported here.
#
# Feed persistence is represented by:
#
#   dairyos.data.models.feed_record.FeedRecord
#
# not by the retired legacy FeedStockORM/feed_stock model.
#
# Milk persistence is represented by:
#
#   dairyos.data.models.milk_production.MilkProduction
#
# Importing the authoritative models registers the application metadata
# required by Alembic.
#

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.feed_record import FeedRecord


# Keep explicit references alive for static inspection and to make the
# migration registration boundary unambiguous.
_AUTHORITATIVE_MODELS = (
    MilkProduction,
    FeedRecord,
)


# Alembic Config object.
config = context.config


# Configure Alembic logging when an ini file is present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# The application's SQLAlchemy metadata is the authoritative migration
# metadata. Schema evolution belongs to Alembic, not runtime create_all().
target_metadata = Base.metadata


def _database_url() -> str:
    """
    Return the same database URL used by the DairyOS application runtime.

    Database credentials have one authoritative source. The application
    database module resolves DAIRYOS_DATABASE_URL / DAIRYOS_DB_* configuration.
    Alembic therefore does not maintain a second hard-coded credential.
    """

    return DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations without opening a database connection."""

    url = _database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the authoritative DairyOS database URL."""

    url = _database_url()

    # Keep the Alembic configuration object consistent with the runtime URL.
    # This is useful for Alembic extensions/hooks that inspect the configured
    # sqlalchemy.url value.
    config.set_main_option(
        "sqlalchemy.url",
        url.replace("%", "%%"),
    )

    connectable = engine_from_config(
        {
            "sqlalchemy.url": url,
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from dairyos.data.database.session import DATABASE_URL, Base
from dairyos.data.models.app_setting import AppSetting
from dairyos.data.models.email_digest_delivery import EmailDigestDelivery
from dairyos.data.models.email_digest_run import EmailDigestRun
from dairyos.data.models.email_sender_setting import EmailSenderSetting
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.user import User

_AUTHORITATIVE_MODELS = (
    MilkProduction,
    FeedRecord,
    User,
    AppSetting,
    EmailSenderSetting,
    EmailDigestRun,
    EmailDigestDelivery,
)

config = context.config

if config.config_file_name is not None:
    # The packaged supervisor configures durable logging before it invokes the
    # migration gate. Alembic's default disables every existing named logger,
    # which silently turns off supervisor diagnostics for the remainder of the
    # installed process. Apply Alembic's handlers without muting application
    # loggers that the migration environment does not own.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    return DATABASE_URL


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    external_connection = config.attributes.get("connection")
    if external_connection is not None:
        context.configure(connection=external_connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return

    url = _database_url()
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    connectable = engine_from_config({"sqlalchemy.url": url}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

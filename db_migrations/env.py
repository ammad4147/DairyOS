from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from dairyos.data.database.session import Base, DATABASE_URL

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.user import User
from dairyos.data.models.app_setting import AppSetting
from dairyos.data.models.email_sender_setting import EmailSenderSetting
from dairyos.data.models.email_digest_run import EmailDigestRun
from dairyos.data.models.email_digest_delivery import EmailDigestDelivery

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
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    return DATABASE_URL


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
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

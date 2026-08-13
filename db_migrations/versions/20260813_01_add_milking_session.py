"""Add persisted milking session to milk production records.

Revision ID: 20260813_01
Revises:

Idempotent by inspection. The DairyOS schema is created by
``Base.metadata.create_all()``, so any given column may already exist before
this revision runs; a bare ``add_column`` turns that ordinary situation into a
failed upgrade.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260813_01"
down_revision = None
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())

    if table not in inspector.get_table_names():
        return set()

    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    columns = _columns("milk_production")

    # An empty database has no milk_production yet -- create_all() builds it,
    # already carrying this column. Altering a table that does not exist is
    # the failure that stopped this chain running end-to-end on any database.
    if not columns:
        return

    if "milking_session" in columns:
        return

    op.add_column(
        "milk_production",
        sa.Column("milking_session", sa.String(), nullable=True),
    )


def downgrade() -> None:
    if "milking_session" not in _columns("milk_production"):
        return

    op.drop_column("milk_production", "milking_session")

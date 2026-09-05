"""Persist governed breeding-entry details in PostgreSQL.

Revision ID: 20260905_03
Revises: 20260905_02

This migration is additive. It preserves every existing breeding record and
adds nullable columns for operator-entered sire/semen and notes.
"""

import sqlalchemy as sa
from alembic import op


revision = "20260905_03"
down_revision = "20260905_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "breeding_records" not in tables:
        raise RuntimeError(
            "breeding_records is missing at 20260905_03; "
            "the migration baseline is inconsistent."
        )

    columns = {
        column["name"]
        for column in inspector.get_columns("breeding_records")
    }

    if "semen_or_bull" not in columns:
        op.add_column(
            "breeding_records",
            sa.Column("semen_or_bull", sa.String(), nullable=True),
        )

    if "notes" not in columns:
        op.add_column(
            "breeding_records",
            sa.Column("notes", sa.String(), nullable=True),
        )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrading breeding detail authority would discard operational "
        "breeding history and is intentionally unsupported."
    )

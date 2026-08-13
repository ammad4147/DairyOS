"""Add persisted milking session to milk production records.

Revision ID: 20260813_01
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "20260813_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "milk_production",
        sa.Column("milking_session", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("milk_production", "milking_session")

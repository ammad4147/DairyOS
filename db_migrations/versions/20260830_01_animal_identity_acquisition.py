"""Add acquisition date and historical/legacy Animal ID to the permanent animal record.

Revision ID: 20260830_01
Revises: 20260828_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260830_01"
down_revision = "20260828_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "animal",
        sa.Column("date_of_acquisition", sa.Date(), nullable=True),
    )
    op.add_column(
        "animal",
        sa.Column("legacy_animal_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_animal_legacy_animal_id",
        "animal",
        ["legacy_animal_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_animal_legacy_animal_id", table_name="animal")
    op.drop_column("animal", "legacy_animal_id")
    op.drop_column("animal", "date_of_acquisition")

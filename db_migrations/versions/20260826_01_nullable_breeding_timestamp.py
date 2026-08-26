"""Allow breeding records without an observed timestamp.

Revision ID: 20260826_01
Revises: 20260825_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260826_01"
down_revision = "20260825_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "breeding_records",
        "timestamp",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    null_count = bind.execute(
        sa.text("SELECT COUNT(*) FROM breeding_records WHERE timestamp IS NULL")
    ).scalar_one()
    if null_count:
        raise RuntimeError(
            "Cannot restore NOT NULL on breeding_records.timestamp while "
            f"{null_count} record(s) have no observed timestamp."
        )

    op.alter_column(
        "breeding_records",
        "timestamp",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

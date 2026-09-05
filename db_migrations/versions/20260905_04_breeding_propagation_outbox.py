"""Add durable Breeding propagation outbox.

Revision ID: 20260905_04
Revises: 20260905_03
"""

import sqlalchemy as sa
from alembic import op


revision = "20260905_04"
down_revision = "20260905_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "breeding_propagation_outbox" in inspector.get_table_names():
        return

    op.create_table(
        "breeding_propagation_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("propagation_id", sa.String(), nullable=False),
        sa.Column("record_id", sa.String(), nullable=False),
        sa.Column("animal_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("propagation_id", name="uq_breeding_propagation_outbox_propagation_id"),
    )
    for name, columns in (
        ("ix_breeding_propagation_outbox_propagation_id", ["propagation_id"]),
        ("ix_breeding_propagation_outbox_record_id", ["record_id"]),
        ("ix_breeding_propagation_outbox_animal_id", ["animal_id"]),
        ("ix_breeding_propagation_outbox_status", ["status"]),
    ):
        op.create_index(name, "breeding_propagation_outbox", columns)


def downgrade() -> None:
    raise RuntimeError(
        "Downgrading the Breeding propagation outbox would remove durable "
        "retry evidence and is intentionally unsupported."
    )

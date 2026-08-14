"""Persist daily milk destination accounting.

Revision ID: 20260815_01
Revises: 20260814_06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260815_01"
down_revision = "20260814_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "milk_dispositions" in inspector.get_table_names():
        return

    op.create_table(
        "milk_dispositions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("production_date", sa.Date(), nullable=False),
        sa.Column("disposition_type", sa.String(), nullable=False),
        sa.Column("quantity_litres", sa.Float(), nullable=False),
        sa.Column("sale_id", sa.String(), nullable=True),
        sa.Column("counterparty", sa.String(), nullable=True),
        sa.Column("selling_price_per_litre", sa.Float(), nullable=True),
        sa.Column("amount_due", sa.Float(), nullable=False, server_default="0"),
        sa.Column("amount_received", sa.Float(), nullable=False, server_default="0"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("recorded_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_milk_dispositions_production_date",
        "milk_dispositions",
        ["production_date"],
    )
    op.create_index(
        "ix_milk_dispositions_sale_id",
        "milk_dispositions",
        ["sale_id"],
    )
    op.create_index(
        "ix_milk_dispositions_date_type",
        "milk_dispositions",
        ["production_date", "disposition_type"],
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "milk_dispositions" not in inspector.get_table_names():
        return
    op.drop_index("ix_milk_dispositions_date_type", table_name="milk_dispositions")
    op.drop_index("ix_milk_dispositions_sale_id", table_name="milk_dispositions")
    op.drop_index("ix_milk_dispositions_production_date", table_name="milk_dispositions")
    op.drop_table("milk_dispositions")

"""Use fixed-point persistence for governed financial authorities.

Revision ID: 20260905_01
Revises: 20260905_00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260905_01"
down_revision = "20260905_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Round legacy binary values once, then persist all new values exactly."""
    with op.batch_alter_table("financial_transactions") as batch:
        batch.alter_column(
            "amount",
            existing_type=sa.Float(),
            type_=sa.Numeric(18, 2),
            postgresql_using="round(amount::numeric, 2)",
        )
        batch.alter_column(
            "unit_rate",
            existing_type=sa.Float(),
            type_=sa.Numeric(18, 6),
            postgresql_using="round(unit_rate::numeric, 6)",
        )

    with op.batch_alter_table("milk_dispositions") as batch:
        batch.alter_column(
            "selling_price_per_litre",
            existing_type=sa.Float(),
            type_=sa.Numeric(18, 6),
            postgresql_using="round(selling_price_per_litre::numeric, 6)",
        )
        batch.alter_column(
            "amount_due",
            existing_type=sa.Float(),
            type_=sa.Numeric(18, 2),
            postgresql_using="round(amount_due::numeric, 2)",
        )
        batch.alter_column(
            "amount_received",
            existing_type=sa.Float(),
            type_=sa.Numeric(18, 2),
            postgresql_using="round(amount_received::numeric, 2)",
        )

    with op.batch_alter_table("coml_records") as batch:
        for column in (
            "feed_cost_per_liter",
            "opex_cost_per_liter",
            "total_coml_per_liter",
        ):
            batch.alter_column(
                column,
                existing_type=sa.Float(),
                type_=sa.Numeric(18, 6),
                postgresql_using=f"round({column}::numeric, 6)",
            )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrading financial precision would reintroduce binary-float accounting "
        "authority and is intentionally unsupported."
    )

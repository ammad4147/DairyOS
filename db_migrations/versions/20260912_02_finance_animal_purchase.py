"""Add the durable standard category for Animal Purchase expenses."""

from alembic import op
import sqlalchemy as sa


revision = "20260912_02"
down_revision = "20260912_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "financial_transactions" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("financial_transactions")}
    if "animal_category" not in columns:
        op.add_column(
            "financial_transactions",
            sa.Column("animal_category", sa.String(), nullable=True),
        )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade would remove Animal Purchase category authority. "
        "Restore a verified compatible backup instead."
    )

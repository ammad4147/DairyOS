"""Persist structured Finance authority on inventory movements.

Revision ID: 20260910_04
Revises: 20260910_03

Existing historical movement notes are not parsed or rewritten. The new
nullable reference applies prospectively and prevents future orphaned links.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260910_04"
down_revision = "20260910_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "inventory_transactions",
        sa.Column(
            "source_financial_transaction_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_inventory_transaction_source_finance",
        "inventory_transactions",
        "financial_transactions",
        ["source_financial_transaction_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_inventory_transactions_source_financial_transaction_id",
        "inventory_transactions",
        ["source_financial_transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    raise RuntimeError(
        "Inventory Finance traceability migration is irreversible in-place. "
        "Restore a verified compatible backup for rollback."
    )

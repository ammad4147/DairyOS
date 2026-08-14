"""Inventory ledger table (G8.1).

Revision ID: 20260814_02
Revises: 20260814_01

Before this migration, `POST /farm/inventory` was event-journal-only: no
queryable stock model existed anywhere, so no report could answer "how much
feed do we have left" without replaying the entire event journal by hand.

Decision (build-spec Session 8, confirmed via AskUserQuestion 2026-08-14):
stock is a transaction ledger, summed on read -- never a separately
maintained running total that could silently drift from its own history.

Direction is fixed per movement type, not left to the reader to infer:
PURCHASE/RECEIPT always increase stock, CONSUMPTION/WASTAGE always decrease
it, and only TRANSFER/ADJUSTMENT carry an operator-entered signed quantity
(a transfer can be inbound or outbound; an adjustment can correct up or
down). See `dairyos.data.models.inventory_transaction.InventoryTransaction`
for the authoritative sign logic.

This is a new table, so there is no historical data to migrate or leave
ambiguous -- unlike the finance/milk migrations before it.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260814_02"
down_revision = "20260814_01"
branch_labels = None
depends_on = None


TABLE = "inventory_transactions"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def upgrade() -> None:
    # No-op on a database that has never created the table (a fresh install
    # builds it from the model metadata, already carrying this shape).
    if _has_table(TABLE):
        return

    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item", sa.String(), nullable=False),
        sa.Column("movement_type", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("signed_quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("supplier", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("recorded_by", sa.String(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    if not _has_table(TABLE):
        return

    op.drop_table(TABLE)

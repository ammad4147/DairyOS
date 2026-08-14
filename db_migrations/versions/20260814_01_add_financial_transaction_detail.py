"""Financial transaction detail columns: payment_method, counterparty, notes.

Revision ID: 20260814_01
Revises: 20260813_02

The API has always accepted ``payment_method``, ``counterparty`` and
``notes`` on ``POST /farm/financial`` and returned 200. Only a single
``reference`` column was ever persisted, populated as
``counterparty or notes or ""`` -- so an entry carrying both a counterparty
and notes lost the notes, and ``payment_method`` was never written to the
ledger at all. Every financial report reads this table, so no report could
ever distinguish cash from bank.

Existing rows are deliberately NOT backfilled. ``reference`` holds either a
counterparty or a note and nothing recorded which; splitting it by guesswork
would fabricate a distinction the data never carried. The new columns stay
NULL on historical rows, which reads correctly as "not recorded" rather than
as an empty value someone entered.

``reference`` is left in place and still written, so anything reading it
continues to work.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260814_01"
down_revision = "20260813_02"
branch_labels = None
depends_on = None


TABLE = "financial_transactions"
NEW_COLUMNS = ("payment_method", "counterparty", "notes")


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _column_names(table: str) -> set[str]:
    if not _has_table(table):
        return set()

    return {column["name"] for column in _inspector().get_columns(table)}


def upgrade() -> None:
    # No-op on a database that has never created the table (a fresh install
    # builds it from the model metadata, already carrying these columns).
    if not _has_table(TABLE):
        return

    existing = _column_names(TABLE)

    for column_name in NEW_COLUMNS:
        if column_name not in existing:
            op.add_column(
                TABLE,
                sa.Column(column_name, sa.String(), nullable=True),
            )


def downgrade() -> None:
    if not _has_table(TABLE):
        return

    existing = _column_names(TABLE)

    # batch_alter_table so this stays valid on SQLite, which cannot DROP
    # COLUMN in place (IM-013 Phase 2 makes SQLite the default engine).
    with op.batch_alter_table(TABLE) as batch:
        for column_name in NEW_COLUMNS:
            if column_name in existing:
                batch.drop_column(column_name)

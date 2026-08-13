"""Milking session ledger and the G1.6 yield-integrity columns.

Revision ID: 20260813_02
Revises: 20260813_01

Three changes, all inspect-then-act:

1. ``milking_session_records`` -- the herd-level ledger.
2. ``milk_production.recorded_at`` / ``session_ledger``.
3. The yield columns lose their ``0.0`` default and become nullable, so that
   "not entered" stops masquerading as "gave nothing".

Existing rows are deliberately NOT rewritten. Their zeros are ambiguous and no
migration can recover which of the two things they meant; inventing that
distinction retroactively would be worse than leaving them legible as
pre-ledger history, which ``session_ledger = false`` already marks them as.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260813_02"
down_revision = "20260813_01"
branch_labels = None
depends_on = None


LEDGER_TABLE = "milking_session_records"
LEDGER_INDEX = "uq_milk_production_ledger_animal_day"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _columns(table: str) -> dict:
    if not _has_table(table):
        return {}

    return {
        column["name"]: column
        for column in _inspector().get_columns(table)
    }


def _index_names(table: str) -> set[str]:
    if not _has_table(table):
        return set()

    return {index["name"] for index in _inspector().get_indexes(table)}


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. The ledger table
    # ------------------------------------------------------------------
    if not _has_table(LEDGER_TABLE):
        op.create_table(
            LEDGER_TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_record_id", sa.String(), nullable=False),
            sa.Column("operational_date", sa.Date(), nullable=False),
            sa.Column("milking_session", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("reason", sa.String(), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
            sa.Column("recorded_by", sa.String(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint(
                "session_record_id",
                name="uq_milking_session_records_record_id",
            ),
            sa.UniqueConstraint(
                "operational_date",
                "milking_session",
                name="uq_milking_session_records_date_session",
            ),
        )

    # ------------------------------------------------------------------
    # 2. New milk_production columns
    # ------------------------------------------------------------------
    existing = _columns("milk_production")

    if existing and "recorded_at" not in existing:
        op.add_column(
            "milk_production",
            sa.Column(
                "recorded_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if existing and "session_ledger" not in existing:
        op.add_column(
            "milk_production",
            sa.Column(
                "session_ledger",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    # ------------------------------------------------------------------
    # 3. Yield columns: nullable, no default
    # ------------------------------------------------------------------
    for column_name in (
        "morning_yield",
        "afternoon_yield",
        "evening_yield",
        "total_yield",
    ):
        column = existing.get(column_name)

        if column is None:
            continue

        if column.get("nullable") and column.get("default") is None:
            continue

        op.alter_column(
            "milk_production",
            column_name,
            existing_type=sa.Float(),
            nullable=True,
            server_default=None,
        )

    # ------------------------------------------------------------------
    # 4. Partial unique index over governed rows only
    # ------------------------------------------------------------------
    if existing and LEDGER_INDEX not in _index_names("milk_production"):
        op.create_index(
            LEDGER_INDEX,
            "milk_production",
            ["animal_id", sa.text("date(production_date)")],
            unique=True,
            postgresql_where=sa.text("session_ledger"),
        )


def downgrade() -> None:
    if LEDGER_INDEX in _index_names("milk_production"):
        op.drop_index(LEDGER_INDEX, table_name="milk_production")

    existing = _columns("milk_production")

    if "session_ledger" in existing:
        op.drop_column("milk_production", "session_ledger")

    if "recorded_at" in existing:
        op.drop_column("milk_production", "recorded_at")

    if _has_table(LEDGER_TABLE):
        op.drop_table(LEDGER_TABLE)

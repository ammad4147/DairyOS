"""Enforce the Milk daily-row total and yield invariant at the database."""

from alembic import op
import sqlalchemy as sa


revision = "20260913_01"
down_revision = "20260912_02"
branch_labels = None
depends_on = None


CONSTRAINT_NAME = "ck_milk_production_yield_integrity"
_MILK_FINITE_NONNEGATIVE = """
(
    (morning_yield IS NULL OR
        (morning_yield >= 0 AND
         morning_yield <= 1.7976931348623157e308))
    AND (afternoon_yield IS NULL OR
        (afternoon_yield >= 0 AND
         afternoon_yield <= 1.7976931348623157e308))
    AND (evening_yield IS NULL OR
        (evening_yield >= 0 AND
         evening_yield <= 1.7976931348623157e308))
    AND (total_yield IS NULL OR
        (total_yield >= 0 AND
         total_yield <= 1.7976931348623157e308))
)
"""

CONSTRAINT_SQL = f"""
(
    (session_ledger = FALSE AND {_MILK_FINITE_NONNEGATIVE})
    OR (
        session_ledger = TRUE
        AND {_MILK_FINITE_NONNEGATIVE}
        AND (
            (
                morning_yield IS NULL
                AND afternoon_yield IS NULL
                AND evening_yield IS NULL
                AND total_yield IS NULL
            )
            OR (
                total_yield IS NOT NULL
                AND ABS(
                    total_yield - (
                        COALESCE(morning_yield, 0.0)
                        + COALESCE(afternoon_yield, 0.0)
                        + COALESCE(evening_yield, 0.0)
                    )
                ) <= 0.000001
            )
        )
    )
)
"""


def _inspector():
    return sa.inspect(op.get_bind())


def _tables() -> set[str]:
    return set(_inspector().get_table_names())


def _columns(table: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table)}


def upgrade() -> None:
    if "milk_production" not in _tables():
        return

    required = {
        "morning_yield",
        "afternoon_yield",
        "evening_yield",
        "total_yield",
        "session_ledger",
    }
    if not required.issubset(_columns("milk_production")):
        return

    connection = op.get_bind()
    invalid = connection.execute(
        sa.text(
            f"SELECT count(*) FROM milk_production WHERE NOT ({CONSTRAINT_SQL})"
        )
    ).scalar_one()
    if invalid:
        raise RuntimeError(
            "Cannot add Milk yield integrity constraint: "
            f"{invalid} existing row(s) have a negative/non-finite value, "
            "a stale governed total, or an incomplete governed NULL total. "
            "Repair the data before applying this migration."
        )

    existing = {
        item.get("name")
        for item in _inspector().get_check_constraints("milk_production")
    }
    if CONSTRAINT_NAME not in existing:
        op.create_check_constraint(
            CONSTRAINT_NAME,
            "milk_production",
            CONSTRAINT_SQL,
        )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade would remove the authoritative Milk yield integrity "
        "constraint. Restore a verified compatible backup instead."
    )

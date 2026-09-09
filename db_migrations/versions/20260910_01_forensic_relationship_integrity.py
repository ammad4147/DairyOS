"""Enforce forensic cross-module relationship and TMR snapshot integrity.

Revision ID: 20260910_01
Revises: 20260909_02

This migration is deliberately fail-closed. It never deletes, rewrites, or
guesses historical farm data in order to make a constraint succeed.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260910_01"
down_revision = "20260909_02"
branch_labels = None
depends_on = None

_DAILY_GROUP = "TMR_DAILY_MATERIALIZED"
_DAILY_INDEX = "uq_feed_ration_daily_materialized_date"


def _orphan_exists(bind, child_table, child_column, parent_table, parent_column):
    query = sa.text(
        f"""
        SELECT 1
        FROM {child_table} child
        LEFT JOIN {parent_table} parent
          ON parent.{parent_column} = child.{child_column}
        WHERE child.{child_column} IS NOT NULL
          AND parent.{parent_column} IS NULL
        LIMIT 1
        """
    )
    return bind.execute(query).fetchone() is not None


def upgrade() -> None:
    bind = op.get_bind()

    checks = (
        (
            "health_observation",
            "health_case_id",
            "health_cases",
            "id",
            "Health observation references a missing health case.",
        ),
        (
            "treatment_record",
            "health_case_id",
            "health_cases",
            "id",
            "Treatment references a missing health case.",
        ),
        (
            "breeding_records",
            "semen_lot_id",
            "semen_lots",
            "id",
            "Breeding record references a missing semen lot.",
        ),
        (
            "semen_stock_movements",
            "breeding_record_id",
            "breeding_records",
            "record_id",
            "Semen movement references a missing breeding record.",
        ),
    )

    for child, child_col, parent, parent_col, message in checks:
        if _orphan_exists(bind, child, child_col, parent, parent_col):
            raise RuntimeError(
                message
                + " Reconcile the historical record explicitly before migration; "
                  "DairyOS will not silently relink or discard it."
            )

    duplicate = bind.execute(
        sa.text(
            """
            SELECT effective_date, COUNT(*)
            FROM feed_ration
            WHERE animal_group = :group_name
            GROUP BY effective_date
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        ),
        {"group_name": _DAILY_GROUP},
    ).fetchone()
    if duplicate is not None:
        raise RuntimeError(
            "Multiple daily TMR materialisations exist for operational date "
            f"{duplicate[0]!r}. Reconcile the historical snapshots explicitly "
            "before migration; DairyOS will not choose one silently."
        )

    op.create_foreign_key(
        "fk_health_observation_case",
        "health_observation",
        "health_cases",
        ["health_case_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_treatment_record_case",
        "treatment_record",
        "health_cases",
        ["health_case_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_breeding_records_semen_lot",
        "breeding_records",
        "semen_lots",
        ["semen_lot_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_semen_stock_movements_breeding_record",
        "semen_stock_movements",
        "breeding_records",
        ["breeding_record_id"],
        ["record_id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        _DAILY_INDEX,
        "feed_ration",
        ["animal_group", "effective_date"],
        unique=True,
        postgresql_where=sa.text(
            "animal_group = 'TMR_DAILY_MATERIALIZED'"
        ),
    )


def downgrade() -> None:
    raise RuntimeError(
        "Forensic relationship-integrity migration is irreversible in-place. "
        "Restore a verified pre-migration backup for rollback."
    )

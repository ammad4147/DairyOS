"""Consolidate legacy runtime schema mutations into Alembic authority.

Revision ID: 20260907_01
Revises: 20260906_04

This migration closes schema gaps historically repaired during normal
application startup by dairyos.data.database.migrations.

It is intentionally idempotent because an established DairyOS database may
already contain some or all of these structures from the former runtime
migration path.

After this revision, packaged DairyOS schema authority belongs exclusively to
the Windows migration gate / Alembic lifecycle. Normal application startup
must not create, alter, or repair database schema.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260907_01"
down_revision = "20260906_04"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return table in _inspector().get_table_names()


def _columns(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    return {
        column["name"]
        for column in _inspector().get_columns(table)
    }


def _indexes(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    return {
        index["name"]
        for index in _inspector().get_indexes(table)
        if index.get("name")
    }


def _unique_column_sets(table: str) -> set[tuple[str, ...]]:
    if not _has_table(table):
        return set()

    result: set[tuple[str, ...]] = set()

    for constraint in _inspector().get_unique_constraints(table):
        columns = constraint.get("column_names") or []
        result.add(tuple(columns))

    return result


def _add_column_if_missing(
    table: str,
    column: sa.Column,
) -> None:
    if column.name not in _columns(table):
        op.add_column(table, column)


def _ensure_feed_inventory_items() -> None:
    table = "feed_inventory_items"

    if not _has_table(table):
        op.create_table(
            table,
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "item",
                sa.String(),
                nullable=False,
            ),
            sa.Column(
                "category",
                sa.String(),
                nullable=False,
            ),
            sa.Column(
                "unit",
                sa.String(),
                nullable=False,
            ),
            sa.Column(
                "location",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "reorder_level",
                sa.Float(),
                nullable=False,
            ),
            sa.Column(
                "active",
                sa.Boolean(),
                nullable=False,
            ),
            sa.Column(
                "notes",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
            ),
        )
    else:
        _add_column_if_missing(
            table,
            sa.Column("category", sa.String(), nullable=True),
        )
        _add_column_if_missing(
            table,
            sa.Column("unit", sa.String(), nullable=True),
        )
        _add_column_if_missing(
            table,
            sa.Column("location", sa.String(), nullable=True),
        )
        _add_column_if_missing(
            table,
            sa.Column("reorder_level", sa.Float(), nullable=True),
        )
        _add_column_if_missing(
            table,
            sa.Column("active", sa.Boolean(), nullable=True),
        )
        _add_column_if_missing(
            table,
            sa.Column("notes", sa.String(), nullable=True),
        )
        _add_column_if_missing(
            table,
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        _add_column_if_missing(
            table,
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    # SQLAlchemy's canonical model declares item unique=True.
    if ("item",) not in _unique_column_sets(table):
        op.create_unique_constraint(
            "uq_feed_inventory_items_item",
            table,
            ["item"],
        )


def _ensure_feed_record() -> None:
    table = "feed_record"

    if not _has_table(table):
        op.create_table(
            table,
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "animal_id",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "group_or_pen",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "feed_type",
                sa.String(),
                nullable=False,
            ),
            sa.Column(
                "quantity_kg",
                sa.Float(),
                nullable=False,
            ),
            sa.Column(
                "feeding_date",
                sa.DateTime(),
                nullable=False,
            ),
            sa.Column(
                "notes",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "status",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "unit_cost_per_kg",
                sa.Float(),
                nullable=True,
            ),
            sa.Column(
                "total_feed_cost",
                sa.Float(),
                nullable=True,
            ),
            sa.Column(
                "cost_basis",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "cost_source_financial_transaction_id",
                sa.Integer(),
                nullable=True,
            ),
        )
        return

    _add_column_if_missing(
        table,
        sa.Column("unit_cost_per_kg", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        table,
        sa.Column("total_feed_cost", sa.Float(), nullable=True),
    )
    _add_column_if_missing(
        table,
        sa.Column("cost_basis", sa.String(), nullable=True),
    )
    _add_column_if_missing(
        table,
        sa.Column(
            "cost_source_financial_transaction_id",
            sa.Integer(),
            nullable=True,
        ),
    )


def _ensure_inventory_transaction_sources() -> None:
    table = "inventory_transactions"

    if not _has_table(table):
        # Earlier authoritative migration 20260814_02 owns initial creation.
        # Reaching this revision without that table is inconsistent.
        raise RuntimeError(
            "inventory_transactions is missing before 20260907_01."
        )

    _add_column_if_missing(
        table,
        sa.Column("source_type", sa.String(), nullable=True),
    )
    _add_column_if_missing(
        table,
        sa.Column("source_id", sa.String(), nullable=True),
    )

    indexes = _indexes(table)

    if "ix_inventory_transactions_source_type" not in indexes:
        op.create_index(
            "ix_inventory_transactions_source_type",
            table,
            ["source_type"],
            unique=False,
        )

    indexes = _indexes(table)

    if "ix_inventory_transactions_source_id" not in indexes:
        op.create_index(
            "ix_inventory_transactions_source_id",
            table,
            ["source_id"],
            unique=False,
        )

    indexes = _indexes(table)

    if "uq_inventory_transaction_source" not in indexes:
        op.create_index(
            "uq_inventory_transaction_source",
            table,
            ["source_type", "source_id"],
            unique=True,
        )


def _ensure_financial_transaction_details() -> None:
    table = "financial_transactions"

    if not _has_table(table):
        raise RuntimeError(
            "financial_transactions is missing before 20260907_01."
        )

    columns = (
        sa.Column("master_category", sa.String(), nullable=True),
        sa.Column("sub_category", sa.String(), nullable=True),
        sa.Column("custom_specification", sa.String(), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("unit_rate", sa.Numeric(18, 6), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("settled_date", sa.Date(), nullable=True),
    )

    for column in columns:
        _add_column_if_missing(table, column)

    # Preserve the historical classification backfill previously performed
    # by migrate_finance_feed_opex(). This mutates data classification, not
    # schema, and must therefore move with the authoritative migration.
    op.execute(
        sa.text(
            """
            UPDATE financial_transactions
            SET master_category = CASE
                WHEN UPPER(COALESCE(category, '')) = 'FEED'
                    THEN 'FEED'
                WHEN UPPER(COALESCE(category, '')) IN (
                    'HEALTH',
                    'BREEDING',
                    'LABOUR',
                    'UTILITIES',
                    'EQUIPMENT',
                    'OTHER_OPERATING'
                )
                    THEN 'OPEX'
                ELSE master_category
            END
            WHERE master_category IS NULL
              AND UPPER(COALESCE(transaction_type, ''))
                  IN ('EXPENSE', 'PAYMENT')
            """
        )
    )


def _ensure_milk_quality_samples() -> None:
    table = "milk_quality_samples"

    if not _has_table(table):
        op.create_table(
            table,
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "quality_date",
                sa.DateTime(),
                nullable=False,
            ),
            sa.Column(
                "fat_pct",
                sa.Float(),
                nullable=False,
            ),
            sa.Column(
                "snf_pct",
                sa.Float(),
                nullable=False,
            ),
            sa.Column(
                "sample_type",
                sa.String(),
                nullable=False,
            ),
            sa.Column(
                "notes",
                sa.String(),
                nullable=True,
            ),
            sa.Column(
                "recorded_by",
                sa.String(),
                nullable=False,
            ),
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
            ),
            sa.Column(
                "recorded_at",
                sa.DateTime(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
            ),
        )

    indexes = _indexes(table)

    if "ix_milk_quality_samples_quality_date" not in indexes:
        op.create_index(
            "ix_milk_quality_samples_quality_date",
            table,
            ["quality_date"],
            unique=False,
        )

    indexes = _indexes(table)

    if "uq_milk_quality_sample_day" not in indexes:
        op.create_index(
            "uq_milk_quality_sample_day",
            table,
            [sa.text("date(quality_date)")],
            unique=True,
            postgresql_where=sa.text(
                "status = 'RECORDED'"
            ),
        )


def upgrade() -> None:
    _ensure_feed_inventory_items()
    _ensure_feed_record()
    _ensure_inventory_transaction_sources()
    _ensure_financial_transaction_details()
    _ensure_milk_quality_samples()


def downgrade() -> None:
    raise RuntimeError(
        "20260907_01 consolidates production persistence authorities. "
        "Downgrade is intentionally unsupported because removing these "
        "tables/columns/indexes could destroy established farm data."
    )

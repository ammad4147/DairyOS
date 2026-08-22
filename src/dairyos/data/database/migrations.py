"""Small, idempotent schema migrations for deployed DairyOS databases.

The project intentionally keeps runtime table creation separate from schema
evolution. This module contains only additive migrations required by
approved feature slices.
"""
from __future__ import annotations

from sqlalchemy import inspect, text

from dairyos.data.database.session import engine


FINANCE_COLUMNS = {
    "master_category": "VARCHAR",
    "sub_category": "VARCHAR",
    "custom_specification": "VARCHAR",
    "quantity": "DOUBLE PRECISION",
    "unit": "VARCHAR",
    "unit_rate": "DOUBLE PRECISION",
    "due_date": "DATE",
    "settled_date": "DATE",
}

MILK_PRODUCTION_COLUMNS = {
    "notes": "VARCHAR",
}

MILK_DISPOSITION_COLUMNS = {
    "status": "VARCHAR NOT NULL DEFAULT 'RECORDED'",
}


def migrate_finance_feed_opex() -> list[str]:
    """Add missing Finance columns without touching existing transactions.

    Existing rows remain nullable. Historical Feed/OPEX classification is still
    backfilled where its meaning is unambiguous.
    """
    changed: list[str] = []

    with engine.begin() as connection:
        inspector = inspect(connection)
        if "financial_transactions" not in inspector.get_table_names():
            return changed

        existing = {column["name"] for column in inspector.get_columns("financial_transactions")}

        for name, sql_type in FINANCE_COLUMNS.items():
            if name in existing:
                continue
            connection.execute(text(f'ALTER TABLE financial_transactions ADD COLUMN "{name}" {sql_type}'))
            changed.append(name)

        if "master_category" in {*(existing), *FINANCE_COLUMNS}:
            connection.execute(
                text(
                    """
                    UPDATE financial_transactions
                    SET master_category = CASE
                        WHEN UPPER(COALESCE(category, '')) = 'FEED' THEN 'FEED'
                        WHEN UPPER(COALESCE(category, '')) IN (
                            'HEALTH', 'BREEDING', 'LABOUR', 'UTILITIES',
                            'EQUIPMENT', 'OTHER_OPERATING'
                        ) THEN 'OPEX'
                        ELSE master_category
                    END
                    WHERE master_category IS NULL
                      AND UPPER(COALESCE(transaction_type, '')) IN ('EXPENSE', 'PAYMENT')
                    """
                )
            )

    return changed


def migrate_milk_crud() -> list[str]:
    """Add the minimal additive fields required for Milk CRUD/auditability."""
    changed: list[str] = []

    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())

        if "milk_production" in tables:
            existing = {column["name"] for column in inspector.get_columns("milk_production")}
            for name, sql_type in MILK_PRODUCTION_COLUMNS.items():
                if name in existing:
                    continue
                connection.execute(text(f'ALTER TABLE milk_production ADD COLUMN "{name}" {sql_type}'))
                changed.append(f"milk_production.{name}")

        if "milk_dispositions" in tables:
            existing = {column["name"] for column in inspector.get_columns("milk_dispositions")}
            for name, sql_type in MILK_DISPOSITION_COLUMNS.items():
                if name in existing:
                    continue
                connection.execute(text(f'ALTER TABLE milk_dispositions ADD COLUMN "{name}" {sql_type}'))
                changed.append(f"milk_dispositions.{name}")

    return changed


def migrate_feed_inventory() -> list[str]:
    """Create the feed item master without storing or altering stock balances."""
    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "feed_inventory_items" in tables:
            return []
        connection.execute(
            text(
                """
                CREATE TABLE feed_inventory_items (
                    id SERIAL PRIMARY KEY,
                    item VARCHAR NOT NULL UNIQUE,
                    category VARCHAR NOT NULL DEFAULT 'FEED',
                    unit VARCHAR NOT NULL DEFAULT 'kg',
                    location VARCHAR NULL,
                    reorder_level DOUBLE PRECISION NOT NULL DEFAULT 0,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    notes VARCHAR NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """
            )
        )
    return ["feed_inventory_items"]


def migrate_milk_quality() -> list[str]:
    """Create the daily milk-quality sample table; no historical rows are altered."""
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "milk_quality_samples" in inspector.get_table_names():
            return []
        connection.execute(
            text(
                """
                CREATE TABLE milk_quality_samples (
                    id SERIAL PRIMARY KEY,
                    quality_date TIMESTAMP NOT NULL,
                    fat_pct DOUBLE PRECISION NOT NULL,
                    snf_pct DOUBLE PRECISION NOT NULL,
                    sample_type VARCHAR NOT NULL DEFAULT 'BULK_TANK',
                    notes VARCHAR NULL,
                    recorded_by VARCHAR NOT NULL DEFAULT 'UI Operator',
                    status VARCHAR NOT NULL DEFAULT 'RECORDED',
                    recorded_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX uq_milk_quality_sample_day ON milk_quality_samples ((DATE(quality_date))) WHERE status = 'RECORDED'"
            )
        )
    return ["milk_quality_samples"]

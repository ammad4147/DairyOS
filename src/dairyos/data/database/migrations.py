"""Small, idempotent schema migrations for deployed DairyOS databases.

The project intentionally keeps runtime table creation separate from schema
evolution. This module contains only additive migrations required by the
Feed/OPEX Finance slice.
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
}


def migrate_finance_feed_opex() -> list[str]:
    """Add missing Feed/OPEX financial columns without touching existing data.

    Existing rows are intentionally left nullable. Historical category values
    are backfilled into master_category where their meaning is unambiguous.
    """
    changed: list[str] = []

    with engine.begin() as connection:
        inspector = inspect(connection)
        if "financial_transactions" not in inspector.get_table_names():
            return changed

        existing = {
            column["name"]
            for column in inspector.get_columns("financial_transactions")
        }

        for name, sql_type in FINANCE_COLUMNS.items():
            if name in existing:
                continue
            connection.execute(
                text(
                    f'ALTER TABLE financial_transactions ADD COLUMN "{name}" {sql_type}'
                )
            )
            changed.append(name)

        # Backfill only expense-affecting legacy rows whose category already
        # carries an unambiguous cost-domain meaning. Income/cash-movement rows
        # remain outside the Feed/OPEX dimension.
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

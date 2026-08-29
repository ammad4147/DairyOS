"""Small, idempotent schema migrations for deployed DairyOS databases.

The project intentionally keeps runtime table creation separate from schema
evolution. This module contains only additive migrations required by
approved feature slices.
"""
from __future__ import annotations

from sqlalchemy import inspect, text

from dairyos.data.database.session import engine

FINANCE_COLUMNS = {
    "master_category": "VARCHAR", "sub_category": "VARCHAR", "custom_specification": "VARCHAR",
    "quantity": "DOUBLE PRECISION", "unit": "VARCHAR", "unit_rate": "DOUBLE PRECISION",
    "due_date": "DATE", "settled_date": "DATE",
}
MILK_PRODUCTION_COLUMNS = {"notes": "VARCHAR"}
MILK_DISPOSITION_COLUMNS = {"status": "VARCHAR NOT NULL DEFAULT 'RECORDED'"}
OPERATIONAL_FINDING_COLUMNS = {"reinstated_at": "TIMESTAMP", "reinstated_by": "VARCHAR", "reinstate_reason": "VARCHAR"}
INVENTORY_SOURCE_COLUMNS = {"source_type": "VARCHAR", "source_id": "VARCHAR"}
FEED_RECORD_COST_COLUMNS = {"unit_cost_per_kg": "DOUBLE PRECISION", "total_feed_cost": "DOUBLE PRECISION", "cost_basis": "VARCHAR", "cost_source_financial_transaction_id": "INTEGER"}


def migrate_finance_feed_opex() -> list[str]:
    changed = []
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "financial_transactions" not in inspector.get_table_names(): return changed
        existing = {c["name"] for c in inspector.get_columns("financial_transactions")}
        for name, sql_type in FINANCE_COLUMNS.items():
            if name not in existing:
                connection.execute(text(f'ALTER TABLE financial_transactions ADD COLUMN "{name}" {sql_type}'))
                changed.append(name)
        if "master_category" in {*existing, *FINANCE_COLUMNS}:
            connection.execute(text("""UPDATE financial_transactions SET master_category = CASE
                WHEN UPPER(COALESCE(category, '')) = 'FEED' THEN 'FEED'
                WHEN UPPER(COALESCE(category, '')) IN ('HEALTH','BREEDING','LABOUR','UTILITIES','EQUIPMENT','OTHER_OPERATING') THEN 'OPEX'
                ELSE master_category END
                WHERE master_category IS NULL AND UPPER(COALESCE(transaction_type, '')) IN ('EXPENSE','PAYMENT')"""))
    return changed


def migrate_milk_crud() -> list[str]:
    changed = []
    with engine.begin() as connection:
        inspector = inspect(connection); tables = set(inspector.get_table_names())
        if "milk_production" in tables:
            existing = {c["name"] for c in inspector.get_columns("milk_production")}
            for name, sql_type in MILK_PRODUCTION_COLUMNS.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE milk_production ADD COLUMN "{name}" {sql_type}')); changed.append(f"milk_production.{name}")
        if "milk_dispositions" in tables:
            existing = {c["name"] for c in inspector.get_columns("milk_dispositions")}
            for name, sql_type in MILK_DISPOSITION_COLUMNS.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE milk_dispositions ADD COLUMN "{name}" {sql_type}')); changed.append(f"milk_dispositions.{name}")
    return changed


def migrate_feed_inventory() -> list[str]:
    changed = []
    with engine.begin() as connection:
        inspector = inspect(connection); tables = set(inspector.get_table_names())
        if "feed_inventory_items" not in tables:
            connection.execute(text("""CREATE TABLE feed_inventory_items (
                id SERIAL PRIMARY KEY, item VARCHAR NOT NULL UNIQUE, category VARCHAR NOT NULL DEFAULT 'FEED',
                unit VARCHAR NOT NULL DEFAULT 'kg', location VARCHAR NULL,
                reorder_level DOUBLE PRECISION NOT NULL DEFAULT 0, active BOOLEAN NOT NULL DEFAULT TRUE,
                notes VARCHAR NULL, created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL)"""))
            changed.append("feed_inventory_items"); tables.add("feed_inventory_items")
        if "inventory_transactions" in tables:
            existing = {c["name"] for c in inspector.get_columns("inventory_transactions")}
            for name, sql_type in INVENTORY_SOURCE_COLUMNS.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE inventory_transactions ADD COLUMN "{name}" {sql_type}')); changed.append(f"inventory_transactions.{name}")
            indexes = {i["name"] for i in inspect(connection).get_indexes("inventory_transactions")}
            if "uq_inventory_transaction_source" not in indexes:
                connection.execute(text("CREATE UNIQUE INDEX uq_inventory_transaction_source ON inventory_transactions (source_type, source_id)")); changed.append("uq_inventory_transaction_source")
        if "feed_record" in tables:
            existing = {c["name"] for c in inspector.get_columns("feed_record")}
            for name, sql_type in FEED_RECORD_COST_COLUMNS.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE feed_record ADD COLUMN "{name}" {sql_type}')); changed.append(f"feed_record.{name}")
    return changed


def migrate_feed_record_costs() -> list[str]:
    return migrate_feed_inventory()


def migrate_milk_quality() -> list[str]:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "milk_quality_samples" in inspector.get_table_names(): return []
        connection.execute(text("""CREATE TABLE milk_quality_samples (
            id SERIAL PRIMARY KEY, quality_date TIMESTAMP NOT NULL, fat_pct DOUBLE PRECISION NOT NULL,
            snf_pct DOUBLE PRECISION NOT NULL, sample_type VARCHAR NOT NULL DEFAULT 'BULK_TANK',
            notes VARCHAR NULL, recorded_by VARCHAR NOT NULL DEFAULT 'UI Operator', status VARCHAR NOT NULL DEFAULT 'RECORDED',
            recorded_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL)"""))
        connection.execute(text("CREATE UNIQUE INDEX uq_milk_quality_sample_day ON milk_quality_samples ((DATE(quality_date))) WHERE status = 'RECORDED'"))
    return ["milk_quality_samples"]


def migrate_coml() -> list[str]:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "coml_records" in inspector.get_table_names(): return []
        connection.execute(text("""CREATE TABLE coml_records (
            id SERIAL PRIMARY KEY, month_start DATE NOT NULL UNIQUE, feed_cost_per_liter DOUBLE PRECISION NOT NULL,
            opex_cost_per_liter DOUBLE PRECISION NOT NULL, total_coml_per_liter DOUBLE PRECISION NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'OFFICIAL', notes VARCHAR NULL, created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL, locked_at TIMESTAMP NOT NULL, updated_by VARCHAR NOT NULL DEFAULT 'UI Operator')"""))
    return ["coml_records"]


def migrate_operational_finding_audit() -> list[str]:
    changed = []
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "operational_findings" not in inspector.get_table_names(): return changed
        existing = {c["name"] for c in inspector.get_columns("operational_findings")}
        for name, sql_type in OPERATIONAL_FINDING_COLUMNS.items():
            if name not in existing:
                connection.execute(text(f'ALTER TABLE operational_findings ADD COLUMN "{name}" {sql_type}')); changed.append(f"operational_findings.{name}")
    return changed


def migrate_payroll() -> list[str]:
    """Create the Finance-owned payroll table additively and idempotently."""
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "payroll_record" in inspector.get_table_names():
            return []
        connection.execute(text("""CREATE TABLE payroll_record (
            id SERIAL PRIMARY KEY,
            employee_name VARCHAR NOT NULL,
            employee_role VARCHAR NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            worked_days NUMERIC(10,2) NOT NULL DEFAULT 0,
            base_pay NUMERIC(14,2) NOT NULL DEFAULT 0,
            overtime_hours NUMERIC(10,2) NOT NULL DEFAULT 0,
            overtime_rate NUMERIC(14,2) NOT NULL DEFAULT 0,
            allowances NUMERIC(14,2) NOT NULL DEFAULT 0,
            advances NUMERIC(14,2) NOT NULL DEFAULT 0,
            deductions NUMERIC(14,2) NOT NULL DEFAULT 0,
            status VARCHAR NOT NULL DEFAULT 'DRAFT',
            payment_date DATE NULL,
            notes TEXT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )"""))
        connection.execute(text("CREATE INDEX ix_payroll_record_employee_name ON payroll_record (employee_name)"))
        connection.execute(text("CREATE INDEX ix_payroll_record_employee_role ON payroll_record (employee_role)"))
        connection.execute(text("CREATE INDEX ix_payroll_record_period_start ON payroll_record (period_start)"))
        connection.execute(text("CREATE INDEX ix_payroll_record_period_end ON payroll_record (period_end)"))
        connection.execute(text("CREATE INDEX ix_payroll_record_status ON payroll_record (status)"))
    return ["payroll_record"]

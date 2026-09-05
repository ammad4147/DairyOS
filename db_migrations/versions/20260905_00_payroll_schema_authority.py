"""Bring the current Finance-owned Payroll schema under Alembic authority.

Revision ID: 20260905_00
Revises: 20260902_02

This migration is deliberately additive and idempotent because deployed
DairyOS databases may already contain the Payroll schema created by the
historical runtime compatibility migration.
"""

import sqlalchemy as sa
from alembic import op


revision = "20260905_00"
down_revision = "20260902_02"
branch_labels = None
depends_on = None


_FINANCE_PAYROLL_INDEX = "ix_financial_transactions_payroll_record_id"
_PAYROLL_FINANCE_INDEX = "ix_payroll_record_finance_transaction_id"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "financial_transactions" not in tables:
        raise RuntimeError(
            "financial_transactions is missing at 20260905_00; "
            "the migration baseline is inconsistent."
        )

    # Finance-side Payroll identity.
    finance_columns = {
        column["name"]
        for column in inspector.get_columns("financial_transactions")
    }

    if "payroll_record_id" not in finance_columns:
        op.add_column(
            "financial_transactions",
            sa.Column("payroll_record_id", sa.Integer(), nullable=True),
        )

    inspector = sa.inspect(bind)
    finance_indexes = {
        index["name"]
        for index in inspector.get_indexes("financial_transactions")
    }

    if _FINANCE_PAYROLL_INDEX not in finance_indexes:
        op.create_index(
            _FINANCE_PAYROLL_INDEX,
            "financial_transactions",
            ["payroll_record_id"],
            unique=False,
        )

    # Payroll record itself.
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "payroll_record" not in tables:
        op.create_table(
            "payroll_record",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("employee_name", sa.String(), nullable=False),
            sa.Column("employee_role", sa.String(), nullable=False),
            sa.Column("period_start", sa.Date(), nullable=False),
            sa.Column("period_end", sa.Date(), nullable=False),
            sa.Column(
                "worked_days",
                sa.Numeric(10, 2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "base_pay",
                sa.Numeric(14, 2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "overtime_hours",
                sa.Numeric(10, 2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "overtime_rate",
                sa.Numeric(14, 2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "allowances",
                sa.Numeric(14, 2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "advances",
                sa.Numeric(14, 2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "deductions",
                sa.Numeric(14, 2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
                server_default="DRAFT",
            ),
            sa.Column("payment_date", sa.Date(), nullable=True),
            sa.Column("finance_transaction_id", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

        op.create_index(
            "ix_payroll_record_employee_name",
            "payroll_record",
            ["employee_name"],
        )
        op.create_index(
            "ix_payroll_record_employee_role",
            "payroll_record",
            ["employee_role"],
        )
        op.create_index(
            "ix_payroll_record_period_start",
            "payroll_record",
            ["period_start"],
        )
        op.create_index(
            "ix_payroll_record_period_end",
            "payroll_record",
            ["period_end"],
        )
        op.create_index(
            "ix_payroll_record_status",
            "payroll_record",
            ["status"],
        )
        op.create_index(
            _PAYROLL_FINANCE_INDEX,
            "payroll_record",
            ["finance_transaction_id"],
            unique=True,
            postgresql_where=sa.text(
                "finance_transaction_id IS NOT NULL"
            ),
        )

    else:
        # Existing runtime-created Payroll schema: preserve it and only supply
        # the approved additive linkage/index where missing.
        inspector = sa.inspect(bind)

        payroll_columns = {
            column["name"]
            for column in inspector.get_columns("payroll_record")
        }

        if "finance_transaction_id" not in payroll_columns:
            op.add_column(
                "payroll_record",
                sa.Column(
                    "finance_transaction_id",
                    sa.Integer(),
                    nullable=True,
                ),
            )

        inspector = sa.inspect(bind)
        payroll_indexes = {
            index["name"]
            for index in inspector.get_indexes("payroll_record")
        }

        if _PAYROLL_FINANCE_INDEX not in payroll_indexes:
            op.create_index(
                _PAYROLL_FINANCE_INDEX,
                "payroll_record",
                ["finance_transaction_id"],
                unique=True,
                postgresql_where=sa.text(
                    "finance_transaction_id IS NOT NULL"
                ),
            )


def downgrade() -> None:
    raise RuntimeError(
        "Payroll schema authority migration is intentionally non-destructive. "
        "DairyOS operational Payroll records must not be removed by downgrade."
    )

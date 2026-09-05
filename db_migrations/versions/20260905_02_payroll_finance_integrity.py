"""Guarantee one active Finance posting per payroll record.

Revision ID: 20260905_02
Revises: 20260905_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260905_02"
down_revision = "20260905_01"
branch_labels = None
depends_on = None


_INDEX_NAME = "uq_financial_transactions_payroll_record_id"


def upgrade() -> None:
    bind = op.get_bind()
    duplicate = bind.execute(
        sa.text(
            """
            SELECT payroll_record_id
            FROM financial_transactions
            WHERE payroll_record_id IS NOT NULL
              AND COALESCE(status, 'RECORDED') <> 'VOID'
            GROUP BY payroll_record_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).fetchone()
    if duplicate is not None:
        raise RuntimeError(
            "Cannot enforce payroll-to-Finance integrity because multiple active "
            f"postings exist for payroll record {duplicate[0]!r}. Reconcile the "
            "historical records before migrating."
        )
    op.create_index(
        _INDEX_NAME,
        "financial_transactions",
        ["payroll_record_id"],
        unique=True,
        postgresql_where=sa.text("payroll_record_id IS NOT NULL AND COALESCE(status, 'RECORDED') <> 'VOID'"),
    )


def downgrade() -> None:
    op.drop_index(_INDEX_NAME, table_name="financial_transactions")

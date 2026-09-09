"""Enforce Feed/Payroll/Finance cross-module reference integrity.

Revision ID: 20260910_03
Revises: 20260910_02

The migration is fail-closed. Existing orphaned or cross-wired references must
be reconciled explicitly; DairyOS never guesses which farm transaction was
intended.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260910_03"
down_revision = "20260910_02"
branch_labels = None
depends_on = None


def _exists(bind, sql: str):
    return bind.execute(sa.text(sql)).fetchone()


def upgrade() -> None:
    bind = op.get_bind()

    orphan_feed = _exists(
        bind,
        """
        SELECT fr.id, fr.cost_source_financial_transaction_id
        FROM feed_record fr
        LEFT JOIN financial_transactions ft
          ON ft.id = fr.cost_source_financial_transaction_id
        WHERE fr.cost_source_financial_transaction_id IS NOT NULL
          AND ft.id IS NULL
        LIMIT 1
        """,
    )
    if orphan_feed is not None:
        raise RuntimeError(
            "Feed record references a missing Finance price-source transaction: "
            f"feed_record.id={orphan_feed[0]!r}, "
            f"financial_transaction_id={orphan_feed[1]!r}. "
            "Reconcile the historical record explicitly before migration."
        )

    orphan_payroll_finance = _exists(
        bind,
        """
        SELECT pr.id, pr.finance_transaction_id
        FROM payroll_record pr
        LEFT JOIN financial_transactions ft
          ON ft.id = pr.finance_transaction_id
        WHERE pr.finance_transaction_id IS NOT NULL
          AND ft.id IS NULL
        LIMIT 1
        """,
    )
    if orphan_payroll_finance is not None:
        raise RuntimeError(
            "Payroll record references a missing Finance transaction: "
            f"payroll_record.id={orphan_payroll_finance[0]!r}, "
            f"finance_transaction_id={orphan_payroll_finance[1]!r}. "
            "Reconcile the historical record explicitly before migration."
        )

    orphan_finance_payroll = _exists(
        bind,
        """
        SELECT ft.id, ft.payroll_record_id
        FROM financial_transactions ft
        LEFT JOIN payroll_record pr
          ON pr.id = ft.payroll_record_id
        WHERE ft.payroll_record_id IS NOT NULL
          AND pr.id IS NULL
        LIMIT 1
        """,
    )
    if orphan_finance_payroll is not None:
        raise RuntimeError(
            "Finance transaction references a missing Payroll record: "
            f"financial_transaction.id={orphan_finance_payroll[0]!r}, "
            f"payroll_record_id={orphan_finance_payroll[1]!r}. "
            "Reconcile the historical record explicitly before migration."
        )

    crossed = _exists(
        bind,
        """
        SELECT pr.id, pr.finance_transaction_id, ft.payroll_record_id
        FROM payroll_record pr
        JOIN financial_transactions ft
          ON ft.id = pr.finance_transaction_id
        WHERE pr.finance_transaction_id IS NOT NULL
          AND ft.payroll_record_id IS NOT NULL
          AND ft.payroll_record_id <> pr.id
        LIMIT 1
        """,
    )
    if crossed is not None:
        raise RuntimeError(
            "Payroll/Finance references are cross-wired: "
            f"payroll_record.id={crossed[0]!r} points to Finance "
            f"{crossed[1]!r}, but that Finance row points to payroll "
            f"{crossed[2]!r}. Reconcile explicitly before migration."
        )

    op.create_foreign_key(
        "fk_feed_record_cost_source_financial_transaction",
        "feed_record",
        "financial_transactions",
        ["cost_source_financial_transaction_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_payroll_record_finance_transaction",
        "payroll_record",
        "financial_transactions",
        ["finance_transaction_id"],
        ["id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_financial_transaction_payroll_record",
        "financial_transactions",
        "payroll_record",
        ["payroll_record_id"],
        ["id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_index(
        "ix_feed_record_cost_source_financial_transaction_id",
        "feed_record",
        ["cost_source_financial_transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    raise RuntimeError(
        "Cross-module reference-integrity migration is irreversible in-place. "
        "Restore a verified pre-migration backup for rollback."
    )

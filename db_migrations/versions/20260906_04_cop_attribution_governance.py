"""Add COP classification and attribution metadata to Finance transactions.

Revision ID: 20260906_04
Revises: 20260906_03
"""
import sqlalchemy as sa
from alembic import op

revision = "20260906_04"
down_revision = "20260906_03"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("financial_transactions", sa.Column("cop_classification", sa.String(), nullable=True))
    op.add_column("financial_transactions", sa.Column("cop_attribution_method", sa.String(), nullable=True))
    op.add_column("financial_transactions", sa.Column("cop_service_date", sa.Date(), nullable=True))
    op.add_column("financial_transactions", sa.Column("cop_coverage_start", sa.Date(), nullable=True))
    op.add_column("financial_transactions", sa.Column("cop_coverage_end", sa.Date(), nullable=True))

def downgrade() -> None:
    op.drop_column("financial_transactions", "cop_coverage_end")
    op.drop_column("financial_transactions", "cop_coverage_start")
    op.drop_column("financial_transactions", "cop_service_date")
    op.drop_column("financial_transactions", "cop_attribution_method")
    op.drop_column("financial_transactions", "cop_classification")

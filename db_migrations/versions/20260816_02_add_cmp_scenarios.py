"""Persist CMP analytical scenarios.

Revision ID: 20260816_02
Revises: 20260816_01

Scenario records are analytical assumptions only. They never modify actual
financial transactions, milk production records, or other authoritative data.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260816_02"
down_revision = "20260816_01"
branch_labels = None
depends_on = None


TABLE = "cmp_scenarios"


def _has_table() -> bool:
    return TABLE in sa.inspect(
        op.get_bind()
    ).get_table_names()


def upgrade() -> None:
    if _has_table():
        return

    op.create_table(
        TABLE,
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "scenario_id",
            sa.String(),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "name",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "period_start",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "period_end",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(),
            nullable=False,
            server_default="PKR",
        ),
        sa.Column(
            "basis",
            sa.String(),
            nullable=False,
            server_default="PERSISTED_ACTUALS",
        ),
        sa.Column(
            "selected_cost_domains",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "assumptions",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "milk_volume_litres",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "eligible_cost",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "cmp_per_litre",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="ACTIVE",
        ),
    )


def downgrade() -> None:
    if _has_table():
        op.drop_table(TABLE)

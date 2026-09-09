"""Complete index parity for forensic health relationship constraints.

Revision ID: 20260910_02
Revises: 20260910_01
"""

from alembic import op

revision = "20260910_02"
down_revision = "20260910_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_health_observation_health_case_id",
        "health_observation",
        ["health_case_id"],
        unique=False,
    )
    op.create_index(
        "ix_treatment_record_health_case_id",
        "treatment_record",
        ["health_case_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_treatment_record_health_case_id",
        table_name="treatment_record",
    )
    op.drop_index(
        "ix_health_observation_health_case_id",
        table_name="health_observation",
    )

"""Allow vaccination schedules to exist before administration."""

from alembic import op
import sqlalchemy as sa


revision = "20260914_01"
down_revision = "20260913_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "vaccinations" not in set(inspector.get_table_names()):
        return
    with op.batch_alter_table("vaccinations") as batch:
        batch.alter_column(
            "administered_date",
            existing_type=sa.Date(),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("vaccinations") as batch:
        batch.alter_column(
            "administered_date",
            existing_type=sa.Date(),
            nullable=False,
        )

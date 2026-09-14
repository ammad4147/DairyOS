"""Add optional local animal passport photo data."""
from alembic import op
import sqlalchemy as sa

revision = "20260915_01"
down_revision = "20260914_01"
branch_labels = None
depends_on = None

def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "animal" not in set(inspector.get_table_names()):
        return
    columns = {column["name"] for column in inspector.get_columns("animal")}
    if "photo_data" not in columns:
        op.add_column("animal", sa.Column("photo_data", sa.Text(), nullable=True))

def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "animal" in set(inspector.get_table_names()):
        columns = {column["name"] for column in inspector.get_columns("animal")}
        if "photo_data" in columns:
            op.drop_column("animal", "photo_data")

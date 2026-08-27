"""Enforce unique milk sale identifiers."""

from alembic import op
import sqlalchemy as sa

revision = "20260828_02"
down_revision = "20260828_01"
branch_labels = None
depends_on = None


_INDEX_NAME = "uq_milk_dispositions_sale_id"


def upgrade() -> None:
    bind = op.get_bind()
    duplicates = bind.execute(
        sa.text(
            """
            SELECT sale_id
            FROM milk_dispositions
            WHERE sale_id IS NOT NULL
            GROUP BY sale_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).fetchone()
    if duplicates is not None:
        raise RuntimeError(
            "Cannot enforce unique milk sale identifiers because duplicate "
            f"sale_id already exists: {duplicates[0]!r}. Resolve the duplicate "
            "historical records before migrating."
        )

    op.create_index(
        _INDEX_NAME,
        "milk_dispositions",
        ["sale_id"],
        unique=True,
        postgresql_where=sa.text("sale_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(_INDEX_NAME, table_name="milk_dispositions")

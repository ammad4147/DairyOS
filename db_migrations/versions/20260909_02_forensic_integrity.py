"""Preserve quality revisions and catalog identity; enforce finite stock and feed links.

Invalid pre-existing rows block the migration. No historical rows are deleted,
coerced or assigned invented parents. The Windows migration gate backs up first.
"""
import sqlalchemy as sa
from alembic import op

revision = "20260909_02"
down_revision = "20260909_01"
branch_labels = None
depends_on = None

ANIMAL_LINKS = ("feed_record", "treatment_record", "health_cases", "breeding_records")


def upgrade():
    connection = op.get_bind()
    nonfinite = connection.execute(sa.text(
        "SELECT id FROM inventory_transactions WHERE NOT "
        "(quantity > '-Infinity'::float8 AND quantity < 'Infinity'::float8 "
        "AND signed_quantity > '-Infinity'::float8 AND signed_quantity < 'Infinity'::float8) LIMIT 20"
    )).scalars().all()
    orphans = {}
    for table in ANIMAL_LINKS:
        rows = connection.execute(sa.text(
            f"SELECT DISTINCT f.animal_id FROM {table} f LEFT JOIN animal a ON a.animal_id=f.animal_id "
            "WHERE f.animal_id IS NOT NULL AND a.animal_id IS NULL LIMIT 20"
        )).scalars().all()
        if rows:
            orphans[table] = rows
    if nonfinite or orphans:
        raise RuntimeError(
            f"Integrity migration blocked: non-finite inventory IDs={nonfinite}; "
            f"orphan animal references={orphans}. Reconcile against the verified backup; no rows were changed."
        )
    op.add_column("feed_inventory_items", sa.Column("display_name", sa.String(), nullable=True))
    op.add_column("milk_quality_samples", sa.Column("revision_history", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")))
    for table in ANIMAL_LINKS:
        op.create_foreign_key(f"fk_{table}_animal", table, "animal", ["animal_id"], ["animal_id"], ondelete="RESTRICT")
    for column in ("quantity", "signed_quantity"):
        op.create_check_constraint(f"ck_inventory_{column}_finite", "inventory_transactions", f"{column} >= -1.7976931348623157e308 AND {column} <= 1.7976931348623157e308")


def downgrade():
    raise RuntimeError("Downgrade would remove integrity guarantees and quality revision history. Restore a verified compatible backup instead.")

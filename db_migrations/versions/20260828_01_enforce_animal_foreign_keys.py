"""Enforce referential integrity for animal-linked health and finance rows."""

from alembic import op
import sqlalchemy as sa


revision = "20260828_01"
down_revision = "20260826_01"
branch_labels = None
depends_on = None


_CONSTRAINTS = (
    (
        "health_observation",
        "health_observation_animal_id_fkey",
        "animal_id",
    ),
    (
        "financial_transactions",
        "financial_transactions_animal_id_fkey",
        "animal_id",
    ),
)

_INDEXES = (
    ("ix_health_observation_animal_id", "health_observation", "animal_id"),
    ("ix_financial_transactions_animal_id", "financial_transactions", "animal_id"),
)


def _assert_no_orphans(connection, table: str, constraint_name: str) -> None:
    orphan_count = connection.execute(
        sa.text(
            f"""
            SELECT count(*)
            FROM public.{table} child
            LEFT JOIN public.animal parent
              ON parent.animal_id = child.animal_id
            WHERE child.animal_id IS NOT NULL
              AND parent.animal_id IS NULL
            """
        )
    ).scalar_one()

    if orphan_count:
        raise RuntimeError(
            f"Cannot create {constraint_name}: {orphan_count} orphaned "
            f"{table}.animal_id value(s) reference no registered animal. "
            "Repair the data before applying this migration."
        )


def upgrade() -> None:
    connection = op.get_bind()

    for table, constraint_name, _column in _CONSTRAINTS:
        _assert_no_orphans(connection, table, constraint_name)

    inspector = sa.inspect(connection)

    for index_name, table, column in _INDEXES:
        existing = {idx["name"] for idx in inspector.get_indexes(table)}
        if index_name not in existing:
            op.create_index(index_name, table, [column], unique=False)

    existing_fks = {
        (table, fk.get("name"))
        for table in ("health_observation", "financial_transactions")
        for fk in inspector.get_foreign_keys(table)
    }

    if ("health_observation", "health_observation_animal_id_fkey") not in existing_fks:
        op.create_foreign_key(
            "health_observation_animal_id_fkey",
            "health_observation",
            "animal",
            ["animal_id"],
            ["animal_id"],
            ondelete="RESTRICT",
        )

    if ("financial_transactions", "financial_transactions_animal_id_fkey") not in existing_fks:
        op.create_foreign_key(
            "financial_transactions_animal_id_fkey",
            "financial_transactions",
            "animal",
            ["animal_id"],
            ["animal_id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    op.drop_constraint(
        "financial_transactions_animal_id_fkey",
        "financial_transactions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "health_observation_animal_id_fkey",
        "health_observation",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_financial_transactions_animal_id",
        table_name="financial_transactions",
    )
    op.drop_index(
        "ix_health_observation_animal_id",
        table_name="health_observation",
    )

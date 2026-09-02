"""Install database-enforced destructive-operation guards.

Revision ID: 20260902_01
Revises: 20260830_01, 20260828_02

The application role is expected to have no DELETE/TRUNCATE grants in a
properly provisioned production cluster. These triggers are an independent
second layer: even an authorized administrative connection must explicitly
opt in to a destructive transaction.
"""

from alembic import op
import sqlalchemy as sa

from dairyos.data.database.destructive_guards import install_destructive_guards


revision = "20260902_01"
down_revision = ("20260830_01", "20260828_02")
branch_labels = None
depends_on = None


def upgrade() -> None:
    install_destructive_guards(op.get_bind())


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    rows = bind.execute(
        sa.text(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
              AND tablename <> 'alembic_version'
            """
        )
    )
    for (table_name,) in rows:
        quoted = bind.dialect.identifier_preparer.quote(table_name)
        bind.execute(sa.text(f"DROP TRIGGER IF EXISTS dairyos_block_truncate ON public.{quoted}"))
        bind.execute(sa.text(f"DROP TRIGGER IF EXISTS dairyos_block_bulk_delete ON public.{quoted}"))

    bind.execute(sa.text("DROP FUNCTION IF EXISTS public.dairyos_install_table_guards()"))
    bind.execute(sa.text("DROP FUNCTION IF EXISTS public.dairyos_block_bulk_delete()"))
    bind.execute(sa.text("DROP FUNCTION IF EXISTS public.dairyos_block_truncate()"))
    bind.execute(sa.text("DROP FUNCTION IF EXISTS public.dairyos_destructive_operation_allowed()"))

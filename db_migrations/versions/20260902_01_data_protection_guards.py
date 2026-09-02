"""Install database-enforced destructive-operation guards.

Revision ID: 20260902_01
Revises: 20260830_01, 20260828_02

The application role is expected to have no DELETE/TRUNCATE grants in a
properly provisioned production cluster.  These triggers are an independent
second layer: even an authorized administrative connection must explicitly
opt in to a destructive transaction.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260902_01"
down_revision = ("20260830_01", "20260828_02")
branch_labels = None
depends_on = None


_GUARD_ROLE = "dairyos_destructive_admin"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    bind.execute(
        sa.text(
            """
            DO $dairyos$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_roles WHERE rolname = 'dairyos_destructive_admin'
                ) THEN
                    CREATE ROLE dairyos_destructive_admin NOLOGIN;
                END IF;
            END
            $dairyos$;
            """
        )
    )

    bind.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.dairyos_destructive_operation_allowed()
            RETURNS boolean
            LANGUAGE sql
            STABLE
            AS $function$
                SELECT
                    COALESCE(
                        current_setting('dairyos.allow_destructive_op', true),
                        'false'
                    ) = 'true'
                    AND pg_has_role(
                        session_user,
                        'dairyos_destructive_admin',
                        'MEMBER'
                    );
            $function$;
            """
        )
    )

    bind.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.dairyos_block_truncate()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $function$
            BEGIN
                IF NOT public.dairyos_destructive_operation_allowed() THEN
                    RAISE EXCEPTION
                        'DairyOS blocked TRUNCATE on %. Set LOCAL dairyos.allow_destructive_op=true inside an authorized administrative transaction.',
                        TG_TABLE_NAME
                        USING ERRCODE = '42501';
                END IF;
                RETURN NULL;
            END;
            $function$;
            """
        )
    )

    bind.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.dairyos_block_bulk_delete()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $function$
            DECLARE
                deleted_count bigint;
            BEGIN
                SELECT count(*) INTO deleted_count FROM dairyos_deleted_rows;

                IF deleted_count > 1
                   AND NOT public.dairyos_destructive_operation_allowed() THEN
                    RAISE EXCEPTION
                        'DairyOS blocked bulk DELETE of % rows from %. Use an authorized administrative transaction with SET LOCAL dairyos.allow_destructive_op=true.',
                        deleted_count,
                        TG_TABLE_NAME
                        USING ERRCODE = '42501';
                END IF;
                RETURN NULL;
            END;
            $function$;
            """
        )
    )

    bind.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.dairyos_install_table_guards()
            RETURNS void
            LANGUAGE plpgsql
            AS $function$
            DECLARE
                item record;
            BEGIN
                FOR item IN
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                      AND tablename <> 'alembic_version'
                LOOP
                    EXECUTE format(
                        'DROP TRIGGER IF EXISTS dairyos_block_truncate ON public.%I',
                        item.tablename
                    );
                    EXECUTE format(
                        'CREATE TRIGGER dairyos_block_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.dairyos_block_truncate()',
                        item.tablename
                    );

                    EXECUTE format(
                        'DROP TRIGGER IF EXISTS dairyos_block_bulk_delete ON public.%I',
                        item.tablename
                    );
                    EXECUTE format(
                        'CREATE TRIGGER dairyos_block_bulk_delete AFTER DELETE ON public.%I REFERENCING OLD TABLE AS dairyos_deleted_rows FOR EACH STATEMENT EXECUTE FUNCTION public.dairyos_block_bulk_delete()',
                        item.tablename
                    );
                END LOOP;
            END;
            $function$;
            """
        )
    )

    bind.execute(sa.text("REVOKE TRUNCATE ON ALL TABLES IN SCHEMA public FROM PUBLIC"))
    bind.execute(sa.text("SELECT public.dairyos_install_table_guards()"))


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

"""Database-enforced destructive-operation circuit breakers.

This module is deliberately idempotent so it can be called by both Alembic
upgrades and the packaged fresh-database bootstrap path (which creates the
canonical ORM schema and stamps the migration heads).
"""

from __future__ import annotations

from sqlalchemy import text


DESTRUCTIVE_ROLE = "dairyos_destructive_admin"


def install_destructive_guards(connection) -> None:
    if connection.dialect.name != "postgresql":
        return

    connection.execute(
        text(
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

    connection.execute(
        text(
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

    connection.execute(
        text(
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

    connection.execute(
        text(
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

    connection.execute(
        text(
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

    connection.execute(text("REVOKE TRUNCATE ON ALL TABLES IN SCHEMA public FROM PUBLIC"))
    connection.execute(text("SELECT public.dairyos_install_table_guards()"))

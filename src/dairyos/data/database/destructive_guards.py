"""Database-enforced destructive-operation circuit breakers.

This module is deliberately idempotent so it can be called by both Alembic
upgrades and the packaged fresh-database bootstrap path (which creates the
canonical ORM schema and stamps the migration heads).
"""

from __future__ import annotations

from sqlalchemy import text


DESTRUCTIVE_ROLE = "dairyos_destructive_admin"



def verify_destructive_guards(connection) -> None:
    """Fail closed when the installed PostgreSQL destructive guards are incomplete.

    Normal DairyOS runtime connections are deliberately unprivileged.  They may
    inspect the catalog but must not recreate owner-controlled functions or
    triggers merely because the database is already at the packaged Alembic
    head.
    """
    if connection.dialect.name != "postgresql":
        return

    role_exists = bool(
        connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_roles
                    WHERE rolname = 'dairyos_destructive_admin'
                )
                """
            )
        ).scalar_one()
    )

    required_functions = {
        "dairyos_destructive_operation_allowed",
        "dairyos_block_truncate",
        "dairyos_block_bulk_delete",
        "dairyos_install_table_guards",
    }
    installed_functions = {
        str(row[0])
        for row in connection.execute(
            text(
                """
                SELECT p.proname
                FROM pg_proc AS p
                JOIN pg_namespace AS n
                  ON n.oid = p.pronamespace
                WHERE n.nspname = 'public'
                  AND p.proname IN (
                    'dairyos_destructive_operation_allowed',
                    'dairyos_block_truncate',
                    'dairyos_block_bulk_delete',
                    'dairyos_install_table_guards'
                  )
                """
            )
        )
    }

    protected_tables = {
        str(row[0])
        for row in connection.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                  AND table_name <> 'alembic_version'
                """
            )
        )
    }

    trigger_rows = connection.execute(
        text(
            """
            SELECT c.relname, t.tgname
            FROM pg_trigger AS t
            JOIN pg_class AS c
              ON c.oid = t.tgrelid
            JOIN pg_namespace AS n
              ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND NOT t.tgisinternal
              AND t.tgname IN (
                'dairyos_block_truncate',
                'dairyos_block_bulk_delete'
              )
            """
        )
    )
    triggers_by_table: dict[str, set[str]] = {}
    for table_name, trigger_name in trigger_rows:
        triggers_by_table.setdefault(str(table_name), set()).add(str(trigger_name))

    missing_functions = sorted(required_functions - installed_functions)
    missing_trigger_tables = sorted(
        table_name
        for table_name in protected_tables
        if triggers_by_table.get(table_name, set())
        != {"dairyos_block_truncate", "dairyos_block_bulk_delete"}
    )

    problems: list[str] = []
    if not role_exists:
        problems.append("role dairyos_destructive_admin is missing")
    if missing_functions:
        problems.append(
            "functions missing: " + ", ".join(missing_functions)
        )
    if missing_trigger_tables:
        problems.append(
            "table guards missing or incomplete: "
            + ", ".join(missing_trigger_tables)
        )

    if problems:
        raise RuntimeError(
            "DairyOS destructive guard verification failed: "
            + "; ".join(problems)
        )

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

"""Security provisioning for DairyOS' private PostgreSQL cluster.

Fresh/legacy private clusters historically used ``dairyos`` as the initdb
bootstrap superuser with loopback ``trust`` authentication.  This module turns
that bootstrap identity into a restricted application login, introduces a
separate administrative owner and read-only backup login, revokes public
connection rights, and writes SCRAM-only pg_hba rules.

The normal backend receives only the application credential.  The migration
credential is exposed transiently to the desktop supervisor and removed by the
migration gate before the backend child is launched.  The backup worker uses
only the read-only backup credential.
"""

from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import secrets
import tempfile
from urllib.parse import quote

import psycopg

from dairyos.windows.private_postgres import PrivatePostgreSQLConfig


SECURITY_VERSION = 1
SECURITY_FILENAME = "security.json"
APP_ROLE = "dairyos"
ADMIN_ROLE = "dairyos_admin"
BACKUP_ROLE = "dairyos_backup"
DESTRUCTIVE_ROLE = "dairyos_destructive_admin"


class PrivateDatabaseSecurityError(RuntimeError):
    """Raised when the managed private database cannot be safely hardened."""


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def security_state_path(config: PrivatePostgreSQLConfig | None = None) -> Path:
    if config is not None:
        return config.data_root.parent / SECURITY_FILENAME
    from dairyos.windows.private_postgres import postgres_data_root

    return postgres_data_root().parent / SECURITY_FILENAME


def security_state_exists(config: PrivatePostgreSQLConfig | None = None) -> bool:
    return security_state_path(config).is_file()


def _protect_windows(plain: bytes) -> bytes:
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    source_buffer = ctypes.create_string_buffer(plain)
    source = _DATA_BLOB(len(plain), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte)))
    target = _DATA_BLOB()
    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    if not crypt32.CryptProtectData(
        ctypes.byref(source),
        "DairyOS database credential",
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(target),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel32.LocalFree(target.pbData)


def _unprotect_windows(cipher: bytes) -> bytes:
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    source_buffer = ctypes.create_string_buffer(cipher)
    source = _DATA_BLOB(len(cipher), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte)))
    target = _DATA_BLOB()
    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    if not crypt32.CryptUnprotectData(
        ctypes.byref(source),
        None,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(target),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel32.LocalFree(target.pbData)


def _protect(value: str) -> dict[str, str]:
    raw = value.encode("utf-8")
    if os.name == "nt":
        encrypted = _protect_windows(raw)
        return {"scheme": "windows-dpapi-user", "value": base64.b64encode(encrypted).decode("ascii")}
    # Non-Windows is used only by source/CI tests; production Windows always
    # uses DPAPI.  Keeping the fallback explicit avoids pretending it is an
    # equivalent protection mechanism.
    return {"scheme": "test-base64", "value": base64.b64encode(raw).decode("ascii")}


def _unprotect(payload: dict[str, str]) -> str:
    encoded = base64.b64decode(payload["value"])
    scheme = payload.get("scheme")
    if scheme == "windows-dpapi-user":
        if os.name != "nt":
            raise PrivateDatabaseSecurityError("Windows-protected DairyOS database credentials cannot be decoded on this host.")
        raw = _unprotect_windows(encoded)
    elif scheme == "test-base64" and os.name != "nt":
        raw = encoded
    else:
        raise PrivateDatabaseSecurityError(f"Unsupported DairyOS credential protection scheme: {scheme!r}")
    return raw.decode("utf-8")


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _read_state(config: PrivatePostgreSQLConfig) -> dict[str, object]:
    path = security_state_path(config)
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrivateDatabaseSecurityError(f"DairyOS database security state is invalid: {path}") from exc
    if not isinstance(payload, dict):
        raise PrivateDatabaseSecurityError(f"DairyOS database security state is not an object: {path}")
    return payload


def _passwords(config: PrivatePostgreSQLConfig) -> tuple[str, str, str]:
    state = _read_state(config)
    if not state:
        raise PrivateDatabaseSecurityError("DairyOS private database security has not been provisioned.")
    try:
        return (
            _unprotect(dict(state["application_password"])),
            _unprotect(dict(state["admin_password"])),
            _unprotect(dict(state["backup_password"])),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PrivateDatabaseSecurityError("DairyOS private database security credentials are incomplete.") from exc


def write_secure_hba(data_root: Path, user: str, database: str) -> None:
    """Write the steady-state SCRAM-only loopback authentication policy."""
    hba = data_root / "pg_hba.conf"
    lines = [
        "# Managed by DairyOS. Role-separated, loopback-only private database.",
        f"local   {database}   {APP_ROLE}                              scram-sha-256",
        f"host    {database}   {APP_ROLE}      127.0.0.1/32             scram-sha-256",
        f"host    {database}   {APP_ROLE}      ::1/128                  scram-sha-256",
        f"local   {database}   {BACKUP_ROLE}                           scram-sha-256",
        f"host    {database}   {BACKUP_ROLE}   127.0.0.1/32             scram-sha-256",
        f"host    {database}   {BACKUP_ROLE}   ::1/128                  scram-sha-256",
        f"local   all          {ADMIN_ROLE}                              scram-sha-256",
        f"host    all          {ADMIN_ROLE}     127.0.0.1/32             scram-sha-256",
        f"host    all          {ADMIN_ROLE}     ::1/128                  scram-sha-256",
        "local   all          all                                      reject",
        "host    all          all             0.0.0.0/0                reject",
        "host    all          all             ::0/0                    reject",
    ]
    hba.write_text("\n".join(lines) + "\n", encoding="utf-8")


def install_steady_state_hba_before_start_if_available() -> bool:
    """Allow private_postgres.start() to avoid reintroducing trust after hardening."""
    from dairyos.windows import private_postgres

    if not security_state_exists():
        return False
    private_postgres._write_pg_hba_conf = write_secure_hba
    return True


def _connect(config: PrivatePostgreSQLConfig, *, user: str, password: str | None, database: str | None = None):
    return psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=database or config.database,
        user=user,
        password=password,
        connect_timeout=10,
        autocommit=True,
    )


def _literal(connection, value: str) -> str:
    # psycopg.sql.Literal renders safely against the active connection.
    from psycopg import sql

    return sql.Literal(value).as_string(connection)



def _transfer_application_ownership(connection) -> None:
    """Move only DairyOS-owned user objects to the administrative owner.

    The historical private cluster is initialized with dairyos as the
    bootstrap superuser. A blanket REASSIGN OWNED would also target objects
    that belong to PostgreSQL's bootstrap identity and can therefore fail on
    database-system dependencies. Restrict transfer to objects in user
    schemas inside the DairyOS database.
    """
    from psycopg import sql

    relation_kinds = {
        "r": "TABLE",
        "p": "TABLE",
        "v": "VIEW",
        "m": "MATERIALIZED VIEW",
        "S": "SEQUENCE",
        "f": "FOREIGN TABLE",
    }
    relations = connection.execute(
        """
        SELECT n.nspname, c.relname, c.relkind
        FROM pg_class AS c
        JOIN pg_namespace AS n ON n.oid = c.relnamespace
        JOIN pg_roles AS r ON r.oid = c.relowner
        WHERE r.rolname = %s
          AND n.nspname <> 'information_schema'
          AND n.nspname NOT LIKE 'pg_%%'
          AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
        ORDER BY n.nspname, c.relname
        """,
        (APP_ROLE,),
    ).fetchall()
    for schema_name, object_name, relkind in relations:
        connection.execute(
            sql.SQL("ALTER {} {}.{} OWNER TO {}").format(
                sql.SQL(relation_kinds[relkind]),
                sql.Identifier(schema_name),
                sql.Identifier(object_name),
                sql.Identifier(ADMIN_ROLE),
            )
        )

    routines = connection.execute(
        """
        SELECT
            n.nspname,
            p.proname,
            pg_get_function_identity_arguments(p.oid),
            p.prokind
        FROM pg_proc AS p
        JOIN pg_namespace AS n ON n.oid = p.pronamespace
        JOIN pg_roles AS r ON r.oid = p.proowner
        WHERE r.rolname = %s
          AND n.nspname <> 'information_schema'
          AND n.nspname NOT LIKE 'pg_%%'
          AND p.prokind IN ('f', 'p')
        ORDER BY n.nspname, p.proname
        """,
        (APP_ROLE,),
    ).fetchall()
    for schema_name, routine_name, identity_arguments, prokind in routines:
        connection.execute(
            sql.SQL("ALTER {} {}.{}({}) OWNER TO {}").format(
                sql.SQL("PROCEDURE" if prokind == "p" else "FUNCTION"),
                sql.Identifier(schema_name),
                sql.Identifier(routine_name),
                sql.SQL(identity_arguments),
                sql.Identifier(ADMIN_ROLE),
            )
        )

    owned_types = connection.execute(
        """
        SELECT n.nspname, t.typname, t.typtype
        FROM pg_type AS t
        JOIN pg_namespace AS n ON n.oid = t.typnamespace
        JOIN pg_roles AS r ON r.oid = t.typowner
        WHERE r.rolname = %s
          AND n.nspname <> 'information_schema'
          AND n.nspname NOT LIKE 'pg_%%'
          AND t.typtype IN ('d', 'e')
        ORDER BY n.nspname, t.typname
        """,
        (APP_ROLE,),
    ).fetchall()
    for schema_name, type_name, typtype in owned_types:
        connection.execute(
            sql.SQL("ALTER {} {}.{} OWNER TO {}").format(
                sql.SQL("DOMAIN" if typtype == "d" else "TYPE"),
                sql.Identifier(schema_name),
                sql.Identifier(type_name),
                sql.Identifier(ADMIN_ROLE),
            )
        )

    schemas = connection.execute(
        """
        SELECT n.nspname
        FROM pg_namespace AS n
        JOIN pg_roles AS r ON r.oid = n.nspowner
        WHERE r.rolname = %s
          AND n.nspname <> 'information_schema'
          AND n.nspname NOT LIKE 'pg_%%'
        ORDER BY n.nspname
        """,
        (APP_ROLE,),
    ).fetchall()
    for (schema_name,) in schemas:
        connection.execute(
            sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                sql.Identifier(schema_name),
                sql.Identifier(ADMIN_ROLE),
            )
        )


def _bootstrap_security(config: PrivatePostgreSQLConfig) -> None:
    app_password = secrets.token_urlsafe(36)
    admin_password = secrets.token_urlsafe(48)
    backup_password = secrets.token_urlsafe(36)

    # A legacy/new private cluster reaches this point through loopback trust as
    # the historical bootstrap role ``dairyos``.  All privileged work is done
    # before that role is demoted.
    with _connect(config, user=config.user, password=None) as connection:
        admin_pw = _literal(connection, admin_password)
        backup_pw = _literal(connection, backup_password)
        app_pw = _literal(connection, app_password)

        connection.execute(
            f"""
            DO $dairyos$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{DESTRUCTIVE_ROLE}') THEN
                    CREATE ROLE {DESTRUCTIVE_ROLE} NOLOGIN;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ADMIN_ROLE}') THEN
                    CREATE ROLE {ADMIN_ROLE} LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD {admin_pw};
                ELSE
                    ALTER ROLE {ADMIN_ROLE} LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD {admin_pw};
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{BACKUP_ROLE}') THEN
                    CREATE ROLE {BACKUP_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD {backup_pw};
                ELSE
                    ALTER ROLE {BACKUP_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD {backup_pw};
                END IF;
            END
            $dairyos$;
            """
        )
        connection.execute(f"GRANT {DESTRUCTIVE_ROLE} TO {ADMIN_ROLE}")
        _transfer_application_ownership(connection)
        connection.execute(f"ALTER DATABASE {config.database} OWNER TO {ADMIN_ROLE}")
        connection.execute(f"REVOKE CONNECT ON DATABASE {config.database} FROM PUBLIC")
        connection.execute(f"GRANT CONNECT ON DATABASE {config.database} TO {APP_ROLE}, {ADMIN_ROLE}, {BACKUP_ROLE}")
        connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        connection.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}, {BACKUP_ROLE}")
        connection.execute(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}")
        connection.execute(f"REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM {APP_ROLE}")
        connection.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {BACKUP_ROLE}")
        connection.execute(f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM {BACKUP_ROLE}")
        connection.execute(f"GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE}")
        connection.execute(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO {BACKUP_ROLE}")
        connection.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE {ADMIN_ROLE} IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO {APP_ROLE}")
        connection.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE {ADMIN_ROLE} IN SCHEMA public GRANT SELECT ON TABLES TO {BACKUP_ROLE}")
        connection.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE {ADMIN_ROLE} IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {APP_ROLE}")
        connection.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE {ADMIN_ROLE} IN SCHEMA public GRANT SELECT ON SEQUENCES TO {BACKUP_ROLE}")

        # Demote the historical bootstrap identity only after ownership and
        # grants have been transferred to the separate administrator.
        connection.execute(
            f"ALTER ROLE {APP_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD {app_pw}"
        )

    _atomic_json(
        security_state_path(config),
        {
            "version": SECURITY_VERSION,
            "application_role": APP_ROLE,
            "admin_role": ADMIN_ROLE,
            "backup_role": BACKUP_ROLE,
            "application_password": _protect(app_password),
            "admin_password": _protect(admin_password),
            "backup_password": _protect(backup_password),
        },
    )

    write_secure_hba(config.data_root, APP_ROLE, config.database)
    with _connect(config, user=ADMIN_ROLE, password=admin_password) as admin:
        admin.execute("SELECT pg_reload_conf()")


def _reassert_privileges(config: PrivatePostgreSQLConfig, admin_password: str) -> None:
    with _connect(config, user=ADMIN_ROLE, password=admin_password) as connection:
        connection.execute(f"REVOKE CONNECT ON DATABASE {config.database} FROM PUBLIC")
        connection.execute(f"GRANT CONNECT ON DATABASE {config.database} TO {APP_ROLE}, {ADMIN_ROLE}, {BACKUP_ROLE}")
        connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        connection.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}, {BACKUP_ROLE}")
        connection.execute(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}")
        connection.execute(f"REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM {APP_ROLE}")
        connection.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {BACKUP_ROLE}")
        connection.execute(f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM {BACKUP_ROLE}")
        connection.execute(f"GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE}")
        connection.execute(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO {BACKUP_ROLE}")
        connection.execute(f"GRANT {DESTRUCTIVE_ROLE} TO {ADMIN_ROLE}")
        connection.execute("SELECT pg_reload_conf()")


def ensure_private_database_security(config: PrivatePostgreSQLConfig) -> None:
    if not security_state_exists(config):
        _bootstrap_security(config)
        return

    app_password, admin_password, backup_password = _passwords(config)
    del app_password, backup_password
    write_secure_hba(config.data_root, APP_ROLE, config.database)
    _reassert_privileges(config, admin_password)


def application_password(config: PrivatePostgreSQLConfig) -> str:
    app, _, _ = _passwords(config)
    return app


def admin_password(config: PrivatePostgreSQLConfig) -> str:
    _, admin, _ = _passwords(config)
    return admin


def backup_password(config: PrivatePostgreSQLConfig) -> str:
    _, _, backup = _passwords(config)
    return backup


def _database_url(config: PrivatePostgreSQLConfig, user: str, password: str, database: str | None = None) -> str:
    return (
        "postgresql+psycopg://"
        f"{quote(user, safe='')}:{quote(password, safe='')}@"
        f"{config.host}:{config.port}/{quote(database or config.database, safe='')}"
    )


def application_database_url(config: PrivatePostgreSQLConfig) -> str:
    return _database_url(config, APP_ROLE, application_password(config))


def admin_database_url(config: PrivatePostgreSQLConfig) -> str:
    return _database_url(config, ADMIN_ROLE, admin_password(config))


def backup_database_url(config: PrivatePostgreSQLConfig) -> str:
    return _database_url(config, BACKUP_ROLE, backup_password(config))

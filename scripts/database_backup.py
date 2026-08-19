"""DairyOS PostgreSQL backup/restore utility.

Usage:
  python scripts/database_backup.py backup --output backups/dairyos.dump
  python scripts/database_backup.py verify --input backups/dairyos.dump
  python scripts/database_backup.py restore --input backups/dairyos.dump --target-url postgresql://...

The utility intentionally delegates to PostgreSQL's pg_dump/pg_restore so the
backup format is native and independently recoverable. It never reports a
backup as successful unless the command exits successfully and the dump can be
inspected by pg_restore.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise SystemExit(f"Required PostgreSQL utility not found on PATH: {binary}")
    return path


def backup(database_url: str, output: Path) -> None:
    pg_dump = _require("pg_dump")
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [pg_dump, "--format=custom", "--no-owner", "--file", str(output), database_url],
        check=True,
    )
    if not output.exists() or output.stat().st_size == 0:
        raise SystemExit("Backup command completed but produced an empty dump")
    verify(output)


def verify(dump: Path) -> None:
    if not dump.exists() or dump.stat().st_size == 0:
        raise SystemExit(f"Backup does not exist or is empty: {dump}")
    pg_restore = _require("pg_restore")
    result = subprocess.run(
        [pg_restore, "--list", str(dump)],
        check=True,
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        raise SystemExit("pg_restore could not enumerate the backup contents")


def restore(dump: Path, target_url: str) -> None:
    verify(dump)
    pg_restore = _require("pg_restore")
    subprocess.run(
        [
            pg_restore,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--dbname",
            target_url,
            str(dump),
        ],
        check=True,
    )


def _database_url_from_environment() -> str | None:
    """Resolve the same explicit URL environment variable used by DairyOS.

    ``DATABASE_URL`` remains supported for generic deployment tooling and
    backwards compatibility, but the application-specific variable wins
    whenever both are present.
    """
    return os.getenv("DAIRYOS_DATABASE_URL") or os.getenv("DATABASE_URL")


def main() -> None:
    parser = argparse.ArgumentParser(description="DairyOS PostgreSQL backup/restore utility")
    parser.add_argument("--database-url", default=_database_url_from_environment())
    sub = parser.add_subparsers(dest="command", required=True)

    backup_parser = sub.add_parser("backup")
    backup_parser.add_argument("--output", type=Path, required=True)

    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--input", type=Path, required=True)

    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("--input", type=Path, required=True)
    restore_parser.add_argument("--target-url", required=True)

    args = parser.parse_args()
    if args.command == "backup":
        if not args.database_url:
            parser.error(
                "backup requires --database-url, DAIRYOS_DATABASE_URL, or DATABASE_URL"
            )
        backup(args.database_url, args.output)
    elif args.command == "verify":
        verify(args.input)
    else:
        restore(args.input, args.target_url)


if __name__ == "__main__":
    main()

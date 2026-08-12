from __future__ import annotations

import argparse

from dairyos.data.database.backup import create_backup, restore_backup, verify_backup_artifact
from dairyos.data.database.session import DATABASE_URL


def main() -> int:
    parser = argparse.ArgumentParser(description="DairyOS PostgreSQL backup/restore")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup")
    backup.add_argument("destination")

    restore = subparsers.add_parser("restore")
    restore.add_argument("source")
    restore.add_argument("--database-url", default=DATABASE_URL)

    args = parser.parse_args()
    if args.command == "backup":
        path = create_backup(DATABASE_URL, args.destination)
        print(verify_backup_artifact(path))
        return 0

    restore_backup(args.database_url, args.source)
    print(f"Restored {args.source} into configured PostgreSQL database")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

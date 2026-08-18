"""Command-line interface for the DairyOS lifecycle subsystem."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .manager import LifecycleError, LifecycleManager, UninstallMode, PURGE_CONFIRMATION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dairyos-lifecycle",
        description="Install, validate, back up, recover, upgrade, and uninstall DairyOS safely.",
    )
    parser.add_argument("--install-root", required=True, help="DairyOS runtime/install directory")
    parser.add_argument("--data-root", default=None, help="Farm data directory; defaults to the platform data root")
    parser.add_argument("--database-url", default=None, help="PostgreSQL SQLAlchemy URL")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install")
    sub.add_parser("validate")

    backup = sub.add_parser("backup")
    backup.add_argument("--label", default="manual")

    restore = sub.add_parser("restore")
    restore.add_argument("backup")

    rollback = sub.add_parser("rollback")
    rollback.add_argument("backup")

    uninstall = sub.add_parser("uninstall")
    uninstall.add_argument(
        "--mode",
        choices=[mode.value for mode in UninstallMode],
        required=True,
    )
    uninstall.add_argument("--confirm", default=None)
    uninstall.add_argument(
        "--no-backup-before-purge",
        action="store_true",
        help="Do not create the automatic pre-purge backup",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manager = LifecycleManager(
        installation_root=Path(args.install_root),
        data_root=Path(args.data_root) if args.data_root else None,
        database_url=args.database_url,
    )

    try:
        if args.command == "install":
            result = manager.install()
            print(json.dumps(result.as_dict(), indent=2))
            return 0

        if args.command == "validate":
            result = manager.validate(require_database=bool(manager.database_url))
            print(json.dumps(result, indent=2, default=str))
            return 0

        if args.command == "backup":
            destination = manager.backup(label=args.label)
            print(destination)
            return 0

        if args.command == "restore":
            manager.restore(args.backup)
            print(f"RESTORED: {args.backup}")
            return 0

        if args.command == "rollback":
            result = manager.rollback(args.backup)
            print(json.dumps(result, indent=2, default=str))
            return 0

        if args.command == "uninstall":
            mode = UninstallMode(args.mode)
            if mode is UninstallMode.PURGE_DATA and args.confirm != PURGE_CONFIRMATION:
                print(
                    f"Permanent purge requires --confirm \"{PURGE_CONFIRMATION}\"",
                    file=sys.stderr,
                )
                return 2
            manager.uninstall(
                mode,
                confirmation=args.confirm,
                backup_before_purge=not args.no_backup_before_purge,
            )
            print(f"UNINSTALLED: {mode.value}")
            return 0

        raise RuntimeError(f"Unhandled lifecycle command: {args.command}")
    except LifecycleError as exc:
        print(f"DairyOS lifecycle error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

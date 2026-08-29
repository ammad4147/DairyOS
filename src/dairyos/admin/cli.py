"""Command-line entry point for the standalone DairyOS Admin Tool."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dairyos.admin.service import AdminService
from dairyos.lifecycle.manager import LifecycleManager


def _service() -> AdminService:
    installation_root = os.environ.get("DAIRYOS_INSTALLATION_ROOT", str(Path.cwd()))
    data_root = os.environ.get("DAIRYOS_DATA_ROOT")
    return AdminService(LifecycleManager(installation_root, data_root=data_root))


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone DairyOS Administration Tool")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    backup = sub.add_parser("backup")
    backup.add_argument("--label", default="admin")
    restore = sub.add_parser("restore")
    restore.add_argument("backup")
    rollback = sub.add_parser("rollback")
    rollback.add_argument("backup")
    reset = sub.add_parser("reset")
    reset.add_argument("--confirm", required=True)
    purge = sub.add_parser("purge")
    purge.add_argument("--confirm", required=True)
    uninstall = sub.add_parser("uninstall")
    uninstall.add_argument("--purge", action="store_true")
    uninstall.add_argument("--confirm")
    args = parser.parse_args()
    service = _service()

    if args.command == "status":
        print(json.dumps(service.status(), indent=2, default=str))
    elif args.command == "backup":
        print(json.dumps(service.backup(args.label).__dict__, indent=2))
    elif args.command == "restore":
        print(json.dumps(service.restore(args.backup).__dict__, indent=2))
    elif args.command == "rollback":
        print(json.dumps(service.rollback(args.backup).__dict__, indent=2))
    elif args.command == "reset":
        print(json.dumps(service.reset(args.confirm).__dict__, indent=2))
    elif args.command == "purge":
        print(json.dumps(service.purge(args.confirm).__dict__, indent=2))
    elif args.command == "uninstall":
        print(json.dumps(service.uninstall(args.purge, args.confirm).__dict__, indent=2))


if __name__ == "__main__":
    main()

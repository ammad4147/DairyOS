"""Authenticated CLI for the standalone DairyOS Admin Tool."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from getpass import getpass
import json
import os
from pathlib import Path

from dairyos.admin import auth
from dairyos.admin.service import AdminService
from dairyos.lifecycle.manager import LifecycleManager


def _service() -> AdminService:
    installation_root = os.environ.get("DAIRYOS_INSTALLATION_ROOT", str(Path.cwd()))
    data_root = os.environ.get("DAIRYOS_DATA_ROOT") or os.environ.get("DAIRYOS_DATA_DIR")
    return AdminService(LifecycleManager(installation_root, data_root=data_root))


def _password() -> str:
    value = os.environ.pop("DAIRYOS_ADMIN_PASSWORD", "")
    return value or getpass("DairyOS Admin password: ")


def _reauth(event: str) -> None:
    auth.require_password(_password(), event=event)


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone DairyOS Administration Tool")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup")
    sub.add_parser("recover")
    sub.add_parser("change-password")
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

    if args.command == "setup":
        password = getpass("Create DairyOS Admin password: ")
        confirmation = getpass("Confirm password: ")
        recovery = auth.setup(password, confirmation)
        print("SAVE THIS RECOVERY KEY:", recovery)
        return

    if args.command == "recover":
        recovery = input("Recovery key: ").strip()
        new_password = getpass("New DairyOS Admin password: ")
        confirmation = getpass("Confirm new password: ")
        next_key = auth.recover_password(recovery, new_password, confirmation)
        print("SAVE THIS NEW RECOVERY KEY:", next_key)
        return

    if args.command == "change-password":
        current = _password()
        new_password = getpass("New DairyOS Admin password: ")
        confirmation = getpass("Confirm new password: ")
        next_key = auth.change_password(current, new_password, confirmation)
        print("SAVE THIS NEW RECOVERY KEY:", next_key)
        return

    if not auth.configured():
        raise SystemExit("Admin password is not configured. Run: dairyos-admin-cli setup")

    service = _service()
    if args.command == "status":
        _reauth("cli-status")
        print(json.dumps(service.status(), indent=2, default=str))
    elif args.command == "backup":
        _reauth("cli-backup")
        print(json.dumps(asdict(service.backup(args.label)), indent=2))
    elif args.command == "restore":
        _reauth("cli-restore")
        print(json.dumps(asdict(service.restore(args.backup)), indent=2))
    elif args.command == "rollback":
        _reauth("cli-rollback")
        print(json.dumps(asdict(service.rollback(args.backup)), indent=2))
    elif args.command == "reset":
        _reauth("cli-reset")
        print(json.dumps(asdict(service.reset(args.confirm)), indent=2))
    elif args.command == "purge":
        _reauth("cli-purge")
        print(json.dumps(asdict(service.purge(args.confirm)), indent=2))
    elif args.command == "uninstall":
        _reauth("cli-uninstall")
        print(json.dumps(asdict(service.uninstall(args.purge, args.confirm)), indent=2))


if __name__ == "__main__":
    main()

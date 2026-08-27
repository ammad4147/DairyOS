"""Start DairyOS as an application.

A packaged application needs one entry point it can launch, point at a data
directory, and health-check.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dairyos-server",
        description="Run the DairyOS application server.",
    )
    parser.add_argument("--host", default=os.environ.get("DAIRYOS_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DAIRYOS_PORT", DEFAULT_PORT)))
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--reload", action="store_true", help="Reload on source changes (development only).")
    parser.add_argument("--log-level", default=os.environ.get("DAIRYOS_LOG_LEVEL", "info"), choices=["critical", "error", "warning", "info", "debug", "trace"])
    parser.add_argument("--print-config", action="store_true")
    return parser


def resolve_configuration(args: argparse.Namespace) -> dict[str, object]:
    if args.data_dir:
        os.environ["DAIRYOS_DATA_DIR"] = str(args.data_dir)
    from dairyos.platform import paths
    return {"host": args.host, "port": args.port, "log_level": args.log_level, "reload": bool(args.reload), "paths": paths.describe()}


def _run_production_startup_gates() -> None:
    """Run the production database startup gate.

    DairyOS is a local farm application. Database schema preparation remains
    mandatory, but application login/password configuration is intentionally
    outside the startup path.
    """
    from dairyos.windows.migrations import migrate_if_needed

    migrate_if_needed()


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # PyInstaller windowed builds do not provide normal console streams.
    # Uvicorn's logging formatter may call isatty() on those streams.
    if getattr(sys, "frozen", False) and os.environ.get("DAIRYOS_BACKEND_MODE") == "1":
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")

    args = build_parser().parse_args(argv)
    configuration = resolve_configuration(args)

    if args.print_config:
        print(json.dumps(configuration, indent=2))
        return 0

    environment = os.getenv("DAIRYOS_ENV", "development").strip().lower()
    if environment in {"production", "staging", "preprod"}:
        try:
            _run_production_startup_gates()
        except Exception as exc:
            print(f"DairyOS startup blocked: {exc}", file=sys.stderr)
            return 1

    try:
        import uvicorn
    except ImportError:
        print("uvicorn is not installed. DairyOS cannot start its server.", file=sys.stderr)
        return 1

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(
            f"DairyOS is binding to {args.host} and will be reachable from "
            f"other devices on this network.",
            file=sys.stderr,
        )

    frozen_backend = (
        getattr(sys, "frozen", False)
        and os.environ.get("DAIRYOS_BACKEND_MODE") == "1"
    )

    uvicorn_kwargs = {
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "reload": args.reload,
    }

    if frozen_backend:
        uvicorn_kwargs["log_config"] = None

    uvicorn.run(
        "dairyos.app:app",
        **uvicorn_kwargs,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

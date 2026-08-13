"""Start DairyOS as an application.

There was previously no way to do this. ``dairyos.app`` builds the ASGI
application, but nothing anywhere called ``uvicorn.run``, so DairyOS could be
imported by a test or a developer's ``uvicorn`` command line and by nothing
else. A packaged application needs one entry point it can launch, point at a
data directory, and health-check.

Usage::

    dairyos-server                          # 127.0.0.1:8000, loopback only
    dairyos-server --host 0.0.0.0           # reachable from phones on the LAN
    dairyos-server --port 8123
    dairyos-server --data-dir D:/DairyData
    dairyos-server --print-config           # resolve everything, start nothing
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
    parser.add_argument(
        "--host",
        default=os.environ.get("DAIRYOS_HOST", DEFAULT_HOST),
        help=(
            "Interface to bind. Defaults to 127.0.0.1 (this machine only). "
            "Use 0.0.0.0 to allow phones and tablets on the farm network to "
            "reach DairyOS."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("DAIRYOS_PORT", DEFAULT_PORT)),
        help=f"Port to listen on (default {DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help=(
            "Directory holding this farm's data. Overrides the platform "
            "default; equivalent to setting DAIRYOS_DATA_DIR."
        ),
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload on source changes (development only).",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("DAIRYOS_LOG_LEVEL", "info"),
        choices=["critical", "error", "warning", "info", "debug", "trace"],
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help=(
            "Resolve host, port and every data path, print them, and exit "
            "without starting the server or touching the database."
        ),
    )
    return parser


def resolve_configuration(args: argparse.Namespace) -> dict[str, object]:
    """Apply --data-dir before anything reads a path, then report the result.

    The order matters: ``DAIRYOS_DATA_DIR`` has to be in the environment before
    the path module resolves anything, or the override silently does nothing.

    Note that this mutates the process environment by design. A caller that
    must not leak the change -- a test, or anything invoking this more than
    once -- is responsible for restoring it.
    """

    if args.data_dir:
        os.environ["DAIRYOS_DATA_DIR"] = str(args.data_dir)

    from dairyos.platform import paths

    return {
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "reload": bool(args.reload),
        "paths": paths.describe(),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configuration = resolve_configuration(args)

    if args.print_config:
        print(json.dumps(configuration, indent=2))
        return 0

    try:
        import uvicorn
    except ImportError:  # pragma: no cover - packaging failure, not logic
        print(
            "uvicorn is not installed. DairyOS cannot start its server.",
            file=sys.stderr,
        )
        return 1

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        # Binding beyond loopback exposes the API to the farm network. Say so
        # plainly: at present DairyOS has authentication but no roles, so
        # anyone who can reach this port can write to it.
        print(
            f"DairyOS is binding to {args.host} and will be reachable from "
            f"other devices on this network.",
            file=sys.stderr,
        )

    uvicorn.run(
        "dairyos.app:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

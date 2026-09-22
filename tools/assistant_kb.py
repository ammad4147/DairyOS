"""Assistant knowledge-base tool: build, check freshness, and revalidate.

Usage (from the repository root)::

    python tools/assistant_kb.py build              # compile YAML -> corpus.json + manifest.json
    python tools/assistant_kb.py check              # validate; non-zero exit on errors or STALE records
    python tools/assistant_kb.py stale              # list records whose DairyOS source changed
    python tools/assistant_kb.py verify --all --reviewer "Name"          # record verification
    python tools/assistant_kb.py verify --id milk.flow --reviewer "Name" # revalidate one record

``verify`` must only be run after a person has re-read the anchored source and
confirmed (or corrected) the record. It is the explicit revalidation step that
clears a STALE record.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dairyos_assistant_tools import kb_build  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("check")
    sub.add_parser("stale")
    verify = sub.add_parser("verify")
    verify.add_argument("--id", action="append", default=[])
    verify.add_argument("--all", action="store_true")
    verify.add_argument("--reviewer", required=True)
    args = parser.parse_args(argv)

    if args.command == "verify":
        if not args.all and not args.id:
            parser.error("verify needs --all or --id")
        when = dt.date.today().isoformat()
        updated = kb_build.verify(ROOT, None if args.all else args.id, reviewer=args.reviewer, when=when)
        print(f"verified {len(updated)} record(s)")
        result = kb_build.build(ROOT)
        kb_build.write(ROOT, result)
        return 0

    result = kb_build.build(ROOT)
    for finding in result.findings:
        print(finding)
    counts = result.manifest["counts"]
    print(
        f"records={counts['total']} servable={counts['servable']} facts={counts['facts']} "
        f"stale={len(result.stale)} errors={len(result.errors)}"
    )
    if args.command == "build":
        kb_build.write(ROOT, result)
        return 1 if result.errors else 0
    if args.command == "stale":
        for rid in result.stale:
            print(rid)
        return 0
    return 1 if (result.errors or result.stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())

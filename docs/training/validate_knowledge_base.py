"""Validate the documentation-only DairyOS training/assistant knowledge base.

This validator is intentionally read-only. It checks JSON shape, unique IDs,
cross-links, and declared repository anchors; it never imports the application
or opens an operational database.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "capability_catalog.json"
CONTENT = sorted(ROOT.glob("*-items.json")) + sorted(ROOT.glob("*-catalog.json")) + [ROOT / "cross-link-aliases.json"]


def main() -> int:
    errors: list[str] = []
    ids: dict[str, Path] = {}
    items: list[tuple[Path, dict]] = []
    for path in CONTENT:
        if not path.exists():
            errors.append(f"missing file: {path.name}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON {path.name}: {exc}")
            continue
        for item in payload.get("items", []):
            item_id = item.get("id")
            if not item_id:
                errors.append(f"{path.name}: item without id")
                continue
            if item_id in ids:
                errors.append(f"duplicate id {item_id}: {ids[item_id].name} and {path.name}")
            ids[item_id] = path
            items.append((path, item))
    for path, item in items:
        item_id = item["id"]
        for related in item.get("related", []):
            if related not in ids:
                errors.append(f"{path.name}:{item_id}: missing related id {related}")
        if item.get("redirect_to") and item["redirect_to"] not in ids:
            errors.append(f"{path.name}:{item_id}: missing redirect target {item['redirect_to']}")
        anchors = item.get("anchors", {})
        for key in ("components", "services", "models", "tests"):
            for anchor in anchors.get(key, []):
                if not (ROOT.parent.parent / anchor).exists():
                    errors.append(f"{path.name}:{item_id}: missing {key} anchor {anchor}")
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        expected = {cap for domain in catalog.get("domains", []) for cap in domain.get("capabilities", [])}
        documented = {item.get("capability") for _, item in items}
        missing = sorted(expected - documented)
        print(f"catalog_capabilities={len(expected)} documented_capabilities={len(documented)}")
        print(f"items={len(items)} missing_capabilities={len(missing)}")
        if missing:
            print("MISSING_CAPABILITIES=" + ",".join(missing))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"catalog failure: {exc}")
    print(f"errors={len(errors)}")
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the Assistant's governed how-to draft from the legacy training set.

This is a reproducible consolidation step, not a review shortcut: imported
items remain DRAFT and therefore cannot be served by a certified build.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "docs" / "training"
CORPUS = ROOT / "docs" / "assistant-knowledge"
OUTPUT = CORPUS / "dairyos" / "how-to-consolidated-draft.json"


def main() -> None:
    existing: set[str] = set()
    for path in CORPUS.rglob("*.json"):
        if path.name == "manifest.json":
            continue
        if path == OUTPUT:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in payload.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                existing.add(item["id"])

    items: list[dict] = []
    seen = set(existing)
    for path in sorted(TRAINING.glob("*.json")):
        if path.name in {"capability_catalog.json", "cross-link-aliases.json"}:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload.get("items", []):
            if not isinstance(raw, dict) or not raw.get("id") or raw["id"] in seen:
                continue
            text = json.dumps(raw, ensure_ascii=False).lower()
            if "simulator" in text:
                continue
            item = {
                "id": raw["id"],
                "class": "DAIRY_KNOWLEDGE" if "disease" in path.name else "DAIRYOS_INSTRUCTION",
                "schema_version": 2,
                "domain": str(raw["id"]).split(".", 1)[0],
                "capability": raw.get("capability", str(raw["id"]).split(".", 1)[-1]),
                "title": raw.get("capability", str(raw["id"])),
                "status": "DRAFT",
                "question": raw.get("question", ""),
                "alternatives": raw.get("alternatives") or [raw.get("question", ""), raw.get("capability", "")],
                "answer": raw.get("answer", ""),
                "scenario": raw.get("scenario", {"given": "", "steps": [], "expected": "", "next": ""}),
                "effects": {
                    "persisted": [],
                    "derived": raw.get("effects", []),
                    "projected": [],
                    "audit": [],
                },
                "related": raw.get("related", []),
                "anchors": raw.get("anchors", {}),
                "safety": raw.get("safety", ""),
                "source_training_file": path.relative_to(ROOT).as_posix(),
            }
            if item["class"] == "DAIRY_KNOWLEDGE":
                item["clinical_safety"] = raw.get(
                    "clinical_safety",
                    "Educational information only; not a diagnosis, prescription, or substitute for veterinary assessment.",
                )
            items.append(item)
            seen.add(item["id"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "schema_version": 2,
        "status": "DRAFT",
        "purpose": "Consolidated how-to coverage awaiting implementation and domain review.",
        "items": items,
        "review": {"implementation": "REQUIRED", "domain": "REQUIRED", "coverage": "REQUIRED"},
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_path = CORPUS / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["corpus_version"] = "0.6.0-draft"
    manifest["generated_at"] = "2026-09-20T00:00:00+00:00"
    manifest["counts"]["total"] = manifest["counts"].get("total", 0) + len(items)
    manifest["counts"]["by_status"]["DRAFT"] = len(items)
    for item in items:
        manifest["counts"]["by_class"][item["class"]] = manifest["counts"]["by_class"].get(item["class"], 0) + 1
    rel = OUTPUT.relative_to(CORPUS).as_posix()
    manifest["files"] = [entry for entry in manifest.get("files", []) if entry.get("path") != rel]
    manifest["files"].append({
        "path": rel,
        "class": "MIXED_DRAFT",
        "domain": "cross-domain-how-to",
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "item_count": len(items),
    })
    manifest["note"] = "Existing approved items plus consolidated how-to coverage; new items remain DRAFT until review."
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"consolidated {len(items)} new draft how-to items into {OUTPUT}")


if __name__ == "__main__":
    main()

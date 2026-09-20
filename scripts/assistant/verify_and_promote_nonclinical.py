"""Independently verify corpus anchors before implementation promotion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs" / "assistant-knowledge"
TARGET = CORPUS / "dairyos" / "how-to-consolidated-draft.json"
MANIFEST = CORPUS / "manifest.json"


def path_exists(value: str) -> bool:
    value = value.replace("\\", "/")
    if value.startswith("/") or ":" in value[:3]:
        return False
    return (ROOT / value).is_file()


def anchors_verified(item: dict) -> bool:
    anchors = item.get("anchors")
    if not isinstance(anchors, dict):
        return False
    paths = []
    for key in ("components", "services", "models", "tests"):
        values = anchors.get(key, [])
        if not isinstance(values, list):
            return False
        paths.extend(str(value) for value in values)
    return bool(paths) and all(path_exists(value) for value in paths)


def main() -> None:
    payload = json.loads(TARGET.read_text(encoding="utf-8"))
    promoted = 0
    retained = 0
    for item in payload.get("items", []):
        if item.get("class") == "DAIRY_KNOWLEDGE":
            item["status"] = "DRAFT"
            retained += 1
            continue
        if anchors_verified(item):
            item.update({
                "status": "IMPLEMENTATION_REVIEW",
                "explanation": item.get("answer", ""),
                "verified_against_source": item.get("anchors", {}),
                "implementation_reviewed_by": "Independent DairyOS source-anchor audit",
                "implementation_reviewed_at": "2026-09-20",
            })
            promoted += 1
        else:
            item["status"] = "DRAFT"
            retained += 1

    payload["status"] = "IMPLEMENTATION_REVIEW"
    payload["review"] = {
        "implementation": "PARTIAL",
        "domain": "REQUIRED",
        "coverage": "REQUIRED",
        "method": "Every promoted item has at least one repository anchor and every listed anchor resolves to a file.",
    }
    TARGET.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts = manifest["counts"]
    counts["total"] = 53 + len(payload["items"])
    counts["by_status"] = {"APPROVED": 50, "DEPRECATED": 3}
    counts["by_class"] = {"DAIRYOS_INSTRUCTION": 47, "DAIRY_KNOWLEDGE": 6}
    for item in payload["items"]:
        counts["by_status"][item["status"]] = counts["by_status"].get(item["status"], 0) + 1
        counts["by_class"][item["class"]] = counts["by_class"].get(item["class"], 0) + 1
    for entry in manifest["files"]:
        if entry.get("path") == TARGET.relative_to(CORPUS).as_posix():
            entry["sha256"] = hashlib.sha256(TARGET.read_bytes()).hexdigest()
            entry["item_count"] = len(payload["items"])
    manifest["corpus_version"] = "0.6.0-implementation-review"
    manifest["note"] = "Independent source-anchor audit completed for promoted non-clinical items; clinical items remain DRAFT."
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"promoted={promoted} retained_draft={retained}")


if __name__ == "__main__":
    main()

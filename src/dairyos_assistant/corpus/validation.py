"""Runtime integrity validation of the compiled knowledge corpus.

The frozen Assistant ships ``corpus.json`` and ``manifest.json``. Before serving,
and in the installed-runtime health check, the corpus is validated here using
the standard library only:

* the manifest's corpus hash matches the corpus actually shipped;
* every count in the manifest reconciles with the records;
* identifiers are unique and ``related`` links resolve;
* required fields are present; dairy records carry provenance; triage records
  carry escalation text; review statuses are known;
* no servable record is STALE (its DairyOS source changed since verification).

Authoring-time governance (source anchors, hashing, the verification lock) lives
in ``dairyos_assistant_tools.kb_build`` and is not part of the frozen package.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3
SERVABLE_REVIEW_STATUSES = frozenset({"VET_REVIEWED", "OWNER_CONFIRMED", "SOURCE_CURATED", "ENGINEERING_VERIFIED"})
REVIEW_STATUSES = SERVABLE_REVIEW_STATUSES | {"PENDING"}
# Backwards-compatible name used by earlier tests and tools.
SERVABLE_STATUSES = SERVABLE_REVIEW_STATUSES


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    message: str
    source: str = ""

    def __str__(self) -> str:  # pragma: no cover - diagnostic convenience
        where = f" [{self.source}]" if self.source else ""
        return f"{self.severity.value} {self.code}{where}: {self.message}"


def load(corpus_root: Path | str) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bytes | None]:
    root = Path(corpus_root)
    corpus_path = root / "corpus.json"
    manifest_path = root / "manifest.json"
    corpus = manifest = None
    raw = None
    if corpus_path.is_file():
        raw = corpus_path.read_bytes()
        corpus = json.loads(raw.decode("utf-8"))
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return corpus, manifest, raw


def validate_corpus(corpus_root: Path | str, repo_root: Path | str | None = None, *, check_manifest: bool = True, **_: Any) -> list[Finding]:
    findings: list[Finding] = []
    corpus, manifest, _raw = load(corpus_root)
    if corpus is None:
        return [Finding("CORPUS_MISSING", Severity.ERROR, "corpus.json not found", str(corpus_root))]
    records = corpus.get("records") or []
    if corpus.get("schema_version") != SCHEMA_VERSION:
        findings.append(Finding("SCHEMA_VERSION", Severity.ERROR, f"expected {SCHEMA_VERSION}, got {corpus.get('schema_version')}"))
    ids = Counter(str(r.get("id")) for r in records)
    for rid, count in ids.items():
        if count > 1:
            findings.append(Finding("DUPLICATE_ID", Severity.ERROR, f"appears {count} times", rid))
    for record in records:
        rid = str(record.get("id"))
        for name in ("title", "summary", "facts", "collection", "kind", "review"):
            if not record.get(name):
                findings.append(Finding("MISSING_FIELD", Severity.ERROR, f"missing {name}", rid))
        for target in record.get("related") or []:
            if target not in ids:
                findings.append(Finding("ORPHAN_RELATION", Severity.ERROR, f"related id {target!r} does not exist", rid))
        status = (record.get("review") or {}).get("status")
        if status not in REVIEW_STATUSES:
            findings.append(Finding("BAD_REVIEW", Severity.ERROR, f"review status {status!r}", rid))
        if status == "VET_REVIEWED" and not (record.get("review") or {}).get("reviewer"):
            findings.append(Finding("REVIEW_WITHOUT_REVIEWER", Severity.ERROR, "VET_REVIEWED needs a named reviewer", rid))
        if record.get("collection") == "dairy" and not record.get("provenance"):
            findings.append(Finding("MISSING_PROVENANCE", Severity.ERROR, "dairy records must cite sources", rid))
        for entry in record.get("provenance") or []:
            if not isinstance(entry, dict) or not entry.get("url") or not entry.get("publisher"):
                findings.append(Finding("MALFORMED_PROVENANCE", Severity.ERROR, f"bad provenance entry {entry!r}", rid))
        safety = record.get("safety") or {}
        if safety.get("class") in {"TRIAGE", "VET_ONLY"} and not safety.get("escalate"):
            findings.append(Finding("MISSING_ESCALATION", Severity.ERROR, "triage record without escalation", rid))
        if record.get("freshness") == "STALE" and record.get("servable", True):
            findings.append(Finding("STALE_RECORD", Severity.ERROR, "DairyOS source changed since verification", rid))
    if check_manifest:
        if manifest is None:
            findings.append(Finding("MANIFEST_MISSING", Severity.ERROR, "manifest.json not found", str(corpus_root)))
        else:
            digest = hashlib.sha256(json.dumps(corpus, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
            if manifest.get("corpus_sha256") != digest:
                findings.append(Finding("MANIFEST_HASH_MISMATCH", Severity.ERROR, "corpus does not match its manifest"))
            counts = manifest.get("counts") or {}
            if counts.get("total") != len(records):
                findings.append(Finding("MANIFEST_COUNT", Severity.ERROR, f"manifest total {counts.get('total')} != {len(records)} records"))
            for name, key in (("by_collection", "collection"), ("by_kind", "kind")):
                actual = dict(Counter(str(r.get(key)) for r in records))
                if counts.get(name) != actual:
                    findings.append(Finding("MANIFEST_COUNT", Severity.ERROR, f"{name} does not reconcile"))
            actual_review = dict(Counter(str((r.get("review") or {}).get("status")) for r in records))
            if counts.get("by_review_status") != actual_review:
                findings.append(Finding("MANIFEST_COUNT", Severity.ERROR, "by_review_status does not reconcile"))
            if counts.get("servable") != sum(1 for r in records if r.get("servable", True)):
                findings.append(Finding("MANIFEST_COUNT", Severity.ERROR, "servable count does not reconcile"))
    return findings


def errors(findings: Iterable[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity is Severity.ERROR]


def codes(findings: Iterable[Finding]) -> set[str]:
    return {f.code for f in findings}


def format_report(findings: Sequence[Finding]) -> str:  # pragma: no cover
    lines = [f"corpus validation: {len(findings)} findings"]
    lines.extend(str(f) for f in findings)
    return "\n".join(lines)

"""Build-time compiler and governance checks for the Assistant knowledge base.

Knowledge is authored as YAML under ``docs/assistant-knowledge/source`` and
compiled into ``docs/assistant-knowledge/corpus.json``, which is the only file
the frozen Assistant reads. Compilation is deterministic: the same sources and
the same repository produce byte-identical output, and every count in the
manifest is computed rather than typed.

Governance enforced here:

* Structure: required fields per record kind, unique identifiers, resolvable
  ``related`` links, known safety classes, escalation text for triage records.
* Provenance: every dairy record cites at least one source from the source
  registry; every DairyOS record carries at least one source anchor.
* Freshness: each DairyOS anchor is hashed (a Python symbol's source segment,
  or the presence of a UI label). The hashes recorded at the last human
  verification live in ``anchors.lock.json``. A record whose anchor has changed
  since verification is marked STALE and ``check`` fails, so knowledge cannot
  quietly stay "approved" after the implementation it describes has moved.
* Review semantics: the review status says who actually reviewed what.
  ``VET_REVIEWED`` requires a named veterinarian; source-curated clinical
  content is labelled as such and is never presented as veterinarian-reviewed.

This module is used by ``tools/assistant_kb.py`` and by the test suite. It is
not imported by the Assistant at runtime and may use PyYAML.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3
KB_DIRNAME = Path("docs") / "assistant-knowledge"
SOURCE_DIR = "source"
REGISTRY_PATH = Path("sources") / "registry.json"
CORPUS_FILE = "corpus.json"
MANIFEST_FILE = "manifest.json"
LOCK_FILE = "anchors.lock.json"

KINDS = {
    "HOWTO", "CONCEPT", "CALCULATION", "DATA_FLOW", "TROUBLESHOOTING", "POLICY",
    "TOPIC", "TRIAGE",
}
COLLECTIONS = {"dairyos", "dairy"}
SAFETY_CLASSES = {"NONE", "EDUCATIONAL", "TRIAGE", "VET_ONLY"}
REVIEW_STATUSES = {
    # A named veterinarian reviewed this exact text.
    "VET_REVIEWED",
    # The farm owner confirmed the content applies to this farm.
    "OWNER_CONFIRMED",
    # Curated from the cited authoritative sources; awaiting veterinary review.
    "SOURCE_CURATED",
    # DairyOS behaviour verified by engineering against the anchored source.
    "ENGINEERING_VERIFIED",
    # Written but not yet verified; never served.
    "PENDING",
}
SERVABLE_REVIEW_STATUSES = frozenset(
    {"VET_REVIEWED", "OWNER_CONFIRMED", "SOURCE_CURATED", "ENGINEERING_VERIFIED"}
)


@dataclass
class Finding:
    code: str
    message: str
    record: str = ""
    severity: str = "ERROR"

    def __str__(self) -> str:
        where = f" [{self.record}]" if self.record else ""
        return f"{self.severity} {self.code}{where}: {self.message}"


@dataclass
class BuildResult:
    corpus: dict[str, Any]
    manifest: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def stale(self) -> list[str]:
        return [r["id"] for r in self.corpus["records"] if r.get("freshness") == "STALE"]


# ---------------------------------------------------------------------------
# Anchors
# ---------------------------------------------------------------------------


def _symbol_segment(source: str, symbol: str) -> str | None:
    """Return the exact source text of ``symbol`` (``name`` or ``Class.name``)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    parts = symbol.split(".")

    def find(nodes, name):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
                return node
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                    return node
        return None

    scope = tree.body
    node = None
    for part in parts:
        node = find(scope, part)
        if node is None:
            return None
        scope = getattr(node, "body", [])
    segment = ast.get_source_segment(source, node)
    if segment is None:
        return None
    decorators = getattr(node, "decorator_list", [])
    prefix = "".join((ast.get_source_segment(source, d) or "") + "\n" for d in decorators)
    return prefix + segment


def anchor_key(anchor: dict[str, Any]) -> str:
    if "symbol" in anchor:
        return f"{anchor['path']}::{anchor['symbol']}"
    return f"{anchor['path']}::text:{anchor.get('text', '')}"


def anchor_hash(repo_root: Path, anchor: dict[str, Any]) -> tuple[str | None, str | None]:
    """Hash an anchor, returning ``(digest, error)``."""
    path = repo_root / anchor["path"]
    if not path.is_file():
        return None, f"anchor file does not exist: {anchor['path']}"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "symbol" in anchor:
        segment = _symbol_segment(text, anchor["symbol"])
        if segment is None:
            return None, f"symbol {anchor['symbol']!r} not found in {anchor['path']}"
        return hashlib.sha256(segment.encode("utf-8")).hexdigest(), None
    label = str(anchor.get("text") or "")
    if not label:
        return None, "anchor needs a symbol or a text label"
    if label not in text:
        return None, f"UI text {label!r} not found in {anchor['path']}"
    # UI labels are presence anchors: the hash changes only if the label is removed.
    return hashlib.sha256(f"present:{label}".encode("utf-8")).hexdigest(), None


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def _git_head(repo_root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - informational only
        return "unknown"


def load_sources(repo_root: Path) -> list[tuple[str, dict[str, Any]]]:
    import yaml  # build-time dependency only

    kb = repo_root / KB_DIRNAME / SOURCE_DIR
    loaded = []
    for path in sorted(kb.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        loaded.append((path.name, document))
    return loaded


def load_lock(repo_root: Path) -> dict[str, Any]:
    path = repo_root / KB_DIRNAME / LOCK_FILE
    if not path.is_file():
        return {"records": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _default_review(collection: str, verified_commit: str, verified_at: str) -> dict[str, Any]:
    if collection == "dairy":
        return {
            "status": "SOURCE_CURATED",
            "curated_by": "DairyOS Assistant V2 engineering",
            "curated_at": verified_at,
            "note": "Curated from the cited sources. Not yet reviewed by a veterinarian.",
        }
    return {
        "status": "ENGINEERING_VERIFIED",
        "verified_by": "DairyOS Assistant V2 engineering",
        "verified_at": verified_at,
        "verified_commit": verified_commit,
    }


def build(repo_root: Path | str) -> BuildResult:
    repo_root = Path(repo_root)
    kb = repo_root / KB_DIRNAME
    registry = json.loads((kb / REGISTRY_PATH).read_text(encoding="utf-8"))
    lock = load_lock(repo_root)
    locked = lock.get("records", {})
    findings: list[Finding] = []
    records: list[dict[str, Any]] = []
    files_meta = []

    for filename, document in load_sources(repo_root):
        collection = document.get("collection")
        domain = document.get("domain")
        items = document.get("records") or []
        if collection not in COLLECTIONS:
            findings.append(Finding("BAD_COLLECTION", f"{filename}: collection {collection!r}"))
        raw = (kb / SOURCE_DIR / filename).read_bytes()
        files_meta.append({
            "path": f"{SOURCE_DIR}/{filename}",
            "collection": collection,
            "domain": domain,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "record_count": len(items),
        })
        for item in items:
            record = dict(item)
            for list_field in ("questions", "keywords", "facts", "steps", "related"):
                if isinstance(record.get(list_field), list):
                    record[list_field] = [str(v) for v in record[list_field]]
            record["collection"] = collection
            record["domain"] = record.get("domain") or domain
            record["source_file"] = filename
            records.append(record)

    ids = Counter(r.get("id") for r in records)
    for rid, count in ids.items():
        if not rid:
            findings.append(Finding("MISSING_ID", "record without id"))
        elif count > 1:
            findings.append(Finding("DUPLICATE_ID", f"appears {count} times", rid))
    known = set(ids)

    for record in records:
        rid = record.get("id", "")
        kind = record.get("kind")
        if kind not in KINDS:
            findings.append(Finding("BAD_KIND", f"kind {kind!r}", rid))
        for required in ("title", "summary", "facts", "questions"):
            if not record.get(required):
                findings.append(Finding("MISSING_FIELD", f"missing {required}", rid))
        for fact in record.get("facts") or []:
            if not isinstance(fact, str) or len(fact) < 12:
                findings.append(Finding("BAD_FACT", f"fact too short or not text: {fact!r}", rid))
        for target in record.get("related") or []:
            if target not in known:
                findings.append(Finding("ORPHAN_RELATION", f"related id {target!r} does not exist", rid))
        safety = record.get("safety") or {"class": "NONE"}
        record["safety"] = safety
        if safety.get("class") not in SAFETY_CLASSES:
            findings.append(Finding("BAD_SAFETY", f"safety class {safety.get('class')!r}", rid))
        if safety.get("class") in {"TRIAGE", "VET_ONLY"} and not safety.get("escalate"):
            findings.append(Finding("MISSING_ESCALATION", "triage records need escalation text", rid))

        if record["collection"] == "dairy":
            provenance = record.get("provenance") or []
            if not provenance:
                findings.append(Finding("MISSING_PROVENANCE", "dairy records must cite sources", rid))
            resolved = []
            for entry in provenance:
                source = registry.get(entry.get("source"))
                if source is None:
                    findings.append(Finding("UNKNOWN_SOURCE", f"source {entry.get('source')!r} not in registry", rid))
                    continue
                if not source.get("url") or not source.get("publisher"):
                    findings.append(Finding("MALFORMED_SOURCE", f"source {entry.get('source')} lacks url or publisher", rid))
                resolved.append({**source, "id": entry.get("source"), "section": entry.get("section")})
            record["provenance"] = resolved
            record["freshness"] = "CURRENT"
        else:
            anchors = record.get("anchors") or []
            if not anchors:
                findings.append(Finding("MISSING_ANCHOR", "DairyOS records need source anchors", rid))
            current = {}
            for anchor in anchors:
                digest, error = anchor_hash(repo_root, anchor)
                if error:
                    findings.append(Finding("BROKEN_ANCHOR", error, rid))
                    continue
                current[anchor_key(anchor)] = digest
            record["anchor_hashes"] = current
            previous = (locked.get(rid) or {}).get("anchors")
            if previous is None:
                record["freshness"] = "UNVERIFIED"
                findings.append(Finding("UNVERIFIED", "no verification lock entry; run verify after review", rid, "WARNING"))
            else:
                changed = sorted(k for k, v in current.items() if previous.get(k) != v)
                record["freshness"] = "STALE" if changed else "CURRENT"
                if changed:
                    record["stale_anchors"] = changed
                    findings.append(Finding("STALE", "source changed since verification: " + ", ".join(changed), rid))

        lock_entry = locked.get(rid) or {}
        review = record.get("review") or lock_entry.get("review") or _default_review(
            record["collection"], lock_entry.get("verified_commit", ""), lock_entry.get("verified_at", "")
        )
        if review.get("status") not in REVIEW_STATUSES:
            findings.append(Finding("BAD_REVIEW", f"review status {review.get('status')!r}", rid))
        if review.get("status") == "VET_REVIEWED" and not review.get("reviewer"):
            findings.append(Finding("REVIEW_WITHOUT_REVIEWER", "VET_REVIEWED needs a named reviewer", rid))
        if record["collection"] == "dairy" and review.get("status") == "ENGINEERING_VERIFIED":
            findings.append(Finding("REVIEW_MISMATCH", "clinical content cannot be engineering-verified", rid))
        record["review"] = review
        record["servable"] = review.get("status") in SERVABLE_REVIEW_STATUSES

    records.sort(key=lambda r: r.get("id", ""))
    by_collection = Counter(r["collection"] for r in records)
    by_domain = Counter(f"{r['collection']}:{r['domain']}" for r in records)
    by_kind = Counter(r.get("kind") for r in records)
    by_review = Counter(r["review"]["status"] for r in records)
    by_freshness = Counter(r["freshness"] for r in records)
    by_safety = Counter(r["safety"]["class"] for r in records)
    used_sources = sorted({p["id"] for r in records for p in r.get("provenance", []) if isinstance(p, dict) and "id" in p})

    corpus = {
        "schema_version": SCHEMA_VERSION,
        "records": records,
    }
    corpus_bytes = json.dumps(corpus, ensure_ascii=False, sort_keys=True).encode("utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "dairyos_source_commit": _git_head(repo_root),
        "counts": {
            "total": len(records),
            "servable": sum(1 for r in records if r["servable"]),
            "by_collection": dict(sorted(by_collection.items())),
            "by_domain": dict(sorted(by_domain.items())),
            "by_kind": dict(sorted(by_kind.items())),
            "by_review_status": dict(sorted(by_review.items())),
            "by_freshness": dict(sorted(by_freshness.items())),
            "by_safety_class": dict(sorted(by_safety.items())),
            "facts": sum(len(r.get("facts") or []) for r in records),
            "sources_cited": len(used_sources),
        },
        "files": files_meta,
        "sources_cited": used_sources,
    }
    # Arithmetic self-check: the counts are computed, so any disagreement is a bug.
    for name in ("by_collection", "by_kind", "by_review_status", "by_freshness", "by_safety_class"):
        if sum(manifest["counts"][name].values()) != manifest["counts"]["total"]:
            findings.append(Finding("MANIFEST_ARITHMETIC", f"{name} does not sum to total"))
    if sum(f["record_count"] for f in files_meta) != len(records):
        findings.append(Finding("MANIFEST_ARITHMETIC", "file record counts do not sum to total"))
    return BuildResult(corpus=corpus, manifest=manifest, findings=findings)


def write(repo_root: Path | str, result: BuildResult) -> None:
    kb = Path(repo_root) / KB_DIRNAME
    (kb / CORPUS_FILE).write_text(
        json.dumps(result.corpus, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8"
    )
    (kb / MANIFEST_FILE).write_text(
        json.dumps(result.manifest, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8"
    )


def verify(repo_root: Path | str, ids: list[str] | None, *, reviewer: str, when: str) -> list[str]:
    """Record the current anchor hashes as verified for the given DairyOS records.

    This is the revalidation step: a human (or an engineering review) has read
    the anchored implementation and confirmed the record still describes it.
    """
    repo_root = Path(repo_root)
    result = build(repo_root)
    lock = load_lock(repo_root)
    entries = lock.setdefault("records", {})
    commit = _git_head(repo_root)
    updated = []
    for record in result.corpus["records"]:
        if record["collection"] != "dairyos":
            continue
        if ids and record["id"] not in ids:
            continue
        entries[record["id"]] = {
            "anchors": record.get("anchor_hashes", {}),
            "verified_commit": commit,
            "verified_at": when,
            "verified_by": reviewer,
        }
        updated.append(record["id"])
    lock["records"] = dict(sorted(entries.items()))
    (repo_root / KB_DIRNAME / LOCK_FILE).write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return updated

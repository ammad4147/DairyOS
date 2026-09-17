"""Integrity validation for the DairyOS Assistant knowledge corpus.

This module replaces ``docs/training/validate_knowledge_base.py``, which had two
demonstrated logic failures:

* It collected items with ``payload.get("items", [])`` at the top level only, so
  every item nested under a grouping key was invisible to every check it ran.
  Nine items were unchecked, which allowed seven duplicate identifiers and one
  broken cross-link to pass as ``errors=0``.
* Its capability-coverage check compared capability strings globally rather than
  per domain, so an item in one domain could satisfy a capability belonging to
  another. That masked two genuinely undocumented capabilities.

Both are fixed here, and both are pinned by regression tests that run the
validator against the legacy corpus and assert the defects are reported.

The module is standard library only and read-only. It never imports the
application, opens a database, or performs any network access.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    message: str
    source: str = ""
    item_id: str = ""

    def __str__(self) -> str:  # pragma: no cover - diagnostic convenience
        where = f" [{self.source}" + (f"::{self.item_id}" if self.item_id else "") + "]"
        return f"{self.severity.value} {self.code}{where} {self.message}"


# ---------------------------------------------------------------------------
# Schema contract
# ---------------------------------------------------------------------------

CLASS_DAIRYOS = "DAIRYOS_INSTRUCTION"
CLASS_KNOWLEDGE = "DAIRY_KNOWLEDGE"
VALID_CLASSES = frozenset({CLASS_DAIRYOS, CLASS_KNOWLEDGE})

STATUS_ORDER: tuple[str, ...] = (
    "INVENTORY",
    "DRAFT",
    "IMPLEMENTATION_REVIEW",
    "DOMAIN_REVIEW",
    "APPROVED",
)
SERVABLE_STATUSES = frozenset({"APPROVED"})
DEPRECATED = "DEPRECATED"
VALID_STATUSES = frozenset(STATUS_ORDER) | {DEPRECATED}

# Cumulative required fields, keyed by the status at which they first apply.
REQUIRED_AT: dict[str, tuple[str, ...]] = {
    "INVENTORY": (
        "id",
        "class",
        "schema_version",
        "domain",
        "capability",
        "title",
        "status",
    ),
    "DRAFT": ("question", "answer", "scenario", "effects", "related"),
    "IMPLEMENTATION_REVIEW": (
        "explanation",
        "alternatives",
        "anchors",
        "verified_against_source",
        "implementation_reviewed_by",
        "implementation_reviewed_at",
    ),
    "DOMAIN_REVIEW": ("perspectives", "exceptions", "correction_path"),
    "APPROVED": ("domain_reviewed_by", "domain_reviewed_at"),
}

REQUIRED_DEPRECATION_FIELDS = ("deprecated_at", "deprecation_reason")

SCENARIO_KEYS = frozenset({"given", "steps", "expected", "next"})
EFFECT_BUCKETS = ("persisted", "derived", "projected", "audit")
PERSPECTIVE_KEYS = (
    "operator",
    "supervisor",
    "finance",
    "veterinary_health",
    "technical",
    "training",
    "troubleshooting",
)
ANCHOR_FILE_KEYS = ("components", "services", "models", "tests")

MIN_ALTERNATIVES = 2

# Class B provenance, required from DOMAIN_REVIEW upward.
KNOWLEDGE_PROVENANCE_FIELDS = ("sources", "clinical_safety", "applicability", "jurisdiction")

# A clinical figure must never appear without a source and a scoped jurisdiction.
CLINICAL_FIGURE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:day|days|hour|hours|week|weeks|mg|ml|IU|dose|doses)\b",
    re.IGNORECASE,
)

# Worked examples must use the reserved fictional namespace.
RESERVED_EXAMPLE_ID = re.compile(r"^EX-[A-Z]{2,4}-\d{3,4}$")
IDENTIFIER_SHAPED = re.compile(r"\b[A-Z]{2,4}-[A-Z]{0,4}-?\d{1,4}\b")

# The promoted source has no Simulator; the corpus must not teach one.
SIMULATOR_MENTION = re.compile(r"\bsimulator\b", re.IGNORECASE)

# Section 9 terminology. Passport categories are singular; herd totals plural.
PASSPORT_CATEGORIES = (
    "Milking",
    "Dry",
    "Heifer",
    "Female Calf",
    "Male Calf",
    "Bull",
)
HERD_TOTAL_LABELS = (
    "Milking Cows",
    "Dry Cows",
    "Heifers",
    "Female Calves",
    "Male Calves",
    "Bulls",
)
# Narrow, unambiguous malformations only. Deliberately conservative: a broad
# contextual rule produced false positives during authoring, so this list
# contains only forms that are wrong under any reading.
TERMINOLOGY_VARIANTS = (
    re.compile(r"\bFemale\s+Calfs\b"),
    re.compile(r"\bMale\s+Calfs\b"),
    re.compile(r"\bHeifer\s+Cows?\b"),
    re.compile(r"\bMilking\s+Cow\b(?!s)"),
    re.compile(r"\bDry\s+Cow\b(?!s)"),
    re.compile(r"\bBull\s+Cows?\b"),
)



# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


@dataclass
class LoadedItem:
    item: dict[str, Any]
    source: str
    nested: bool
    path_in_file: str

    @property
    def id(self) -> str:
        value = self.item.get("id")
        return value if isinstance(value, str) else ""


@dataclass
class LoadedCorpus:
    items: list[LoadedItem] = field(default_factory=list)
    manifest: dict[str, Any] | None = None
    files: list[Path] = field(default_factory=list)
    load_findings: list[Finding] = field(default_factory=list)


def _looks_like_item(node: dict[str, Any]) -> bool:
    """An item carries an id plus at least one content or pointer field.

    The legacy validator's blind spot began with a narrower test than this, so
    the predicate is deliberately generous: an alias entry carrying only
    ``id``/``capability``/``redirect_to`` still counts, because a duplicate
    identifier between an alias and a real item is exactly the collision that
    went undetected.
    """
    if not isinstance(node.get("id"), str):
        return False
    if "capabilities" in node:  # a catalogue domain, not an item
        return False
    return any(
        key in node
        for key in ("question", "name", "capability", "redirect_to", "title")
    )


def _walk(node: Any, source: str, trail: str) -> Iterator[tuple[dict[str, Any], str]]:
    if isinstance(node, dict):
        if _looks_like_item(node):
            yield node, trail
            return
        for key, value in node.items():
            yield from _walk(value, source, f"{trail}.{key}" if trail else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, source, f"{trail}[{index}]")


def load_corpus(corpus_root: Path) -> LoadedCorpus:
    """Read every JSON file under ``corpus_root``, walking to any depth."""
    loaded = LoadedCorpus()
    corpus_root = Path(corpus_root)
    if not corpus_root.is_dir():
        loaded.load_findings.append(
            Finding(
                "CORPUS_ROOT_MISSING",
                Severity.ERROR,
                f"corpus root does not exist: {corpus_root}",
                source=str(corpus_root),
            )
        )
        return loaded

    for path in sorted(corpus_root.rglob("*.json")):
        rel = path.relative_to(corpus_root).as_posix()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            loaded.load_findings.append(
                Finding("INVALID_JSON", Severity.ERROR, str(exc), source=rel)
            )
            continue

        loaded.files.append(path)

        if rel in {"manifest.json"}:
            loaded.manifest = payload
            continue
        if path.name == "capability_catalog.json":
            continue

        top_level_ids = {
            item.get("id")
            for item in payload.get("items", [])
            if isinstance(item, dict)
        }
        for item, trail in _walk(payload, rel, ""):
            nested = item.get("id") not in top_level_ids
            loaded.items.append(
                LoadedItem(item=item, source=rel, nested=nested, path_in_file=trail)
            )

    return loaded


def _load_catalogue(corpus_root: Path, repo_root: Path) -> dict[str, set[str]]:
    """Return ``{domain_id: {capability, ...}}`` from whichever catalogue exists."""
    for candidate in (
        Path(corpus_root) / "capability_catalog.json",
        Path(repo_root) / "docs" / "training" / "capability_catalog.json",
    ):
        if candidate.is_file():
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {}
            return {
                domain.get("id", ""): set(domain.get("capabilities", []) or [])
                for domain in payload.get("domains", [])
                if isinstance(domain, dict)
            }
    return {}


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _rendered_text(item: dict[str, Any]) -> str:
    """Every operator-visible string in one blob, for text-level rules."""
    skip = {"anchors", "verified_against_source", "merged_from", "authoring_note", "fix_note"}
    return json.dumps({k: v for k, v in item.items() if k not in skip}, ensure_ascii=False)


def _required_fields_for(status: str) -> tuple[str, ...]:
    if status == DEPRECATED:
        return REQUIRED_AT["INVENTORY"] + REQUIRED_DEPRECATION_FIELDS
    required: list[str] = []
    for level in STATUS_ORDER:
        required.extend(REQUIRED_AT[level])
        if level == status:
            break
    return tuple(required)


def _check_structure(loaded: LoadedCorpus, strict_layout: bool) -> list[Finding]:
    findings: list[Finding] = []
    for entry in loaded.items:
        if entry.nested and strict_layout:
            findings.append(
                Finding(
                    "NESTED_ITEM",
                    Severity.ERROR,
                    "item is not in the file's top-level 'items' array "
                    f"(found at {entry.path_in_file}); nesting is forbidden because "
                    "it hid nine items from the previous validator",
                    source=entry.source,
                    item_id=entry.id,
                )
            )
        for inherited in ("domain", "status", "class"):
            if inherited not in entry.item and strict_layout:
                findings.append(
                    Finding(
                        "INHERITED_FIELD",
                        Severity.ERROR,
                        f"'{inherited}' must be carried explicitly on the item, "
                        "not inherited from the file or a grouping key",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )
    return findings


def _check_identifiers(loaded: LoadedCorpus) -> list[Finding]:
    findings: list[Finding] = []
    seen: dict[str, list[LoadedItem]] = {}
    for entry in loaded.items:
        if not entry.id:
            findings.append(
                Finding(
                    "ITEM_WITHOUT_ID",
                    Severity.ERROR,
                    f"item at {entry.path_in_file} has no string id",
                    source=entry.source,
                )
            )
            continue
        seen.setdefault(entry.id, []).append(entry)

    for item_id, entries in sorted(seen.items()):
        if len(entries) > 1:
            where = ", ".join(
                f"{e.source}{' [alias]' if 'redirect_to' in e.item else ''}"
                for e in entries
            )
            findings.append(
                Finding(
                    "DUPLICATE_ID",
                    Severity.ERROR,
                    f"identifier defined {len(entries)} times: {where}",
                    item_id=item_id,
                )
            )
    return findings


def _check_cross_links(
    loaded: LoadedCorpus, pending_external_ids: frozenset[str]
) -> list[Finding]:
    """Resolve every ``related`` and ``redirect_to`` target.

    During incremental migration a migrated domain legitimately points at items
    that still live only in the legacy corpus. Those are reported as
    ``PENDING_MIGRATION_REF`` warnings rather than errors, so the real state is
    visible without suppressing it. A target that resolves in neither corpus is
    an error, which is how a reference invented during authoring gets caught.
    """
    known = {entry.id for entry in loaded.items if entry.id}
    for entry in loaded.items:
        known.update(entry.item.get("aliases", []) or [])

    findings: list[Finding] = []

    def classify(kind: str, target: str, entry: LoadedItem) -> None:
        if target in known:
            return
        if target in pending_external_ids:
            findings.append(
                Finding(
                    "PENDING_MIGRATION_REF",
                    Severity.WARNING,
                    f"{kind} target {target!r} is not migrated yet; it still "
                    "resolves only in the legacy corpus",
                    source=entry.source,
                    item_id=entry.id,
                )
            )
            return
        findings.append(
            Finding(
                f"BROKEN_{kind.upper()}",
                Severity.ERROR,
                f"{kind} id does not resolve in either corpus: {target}",
                source=entry.source,
                item_id=entry.id,
            )
        )

    for entry in loaded.items:
        for target in entry.item.get("related", []) or []:
            classify("related", target, entry)
        redirect = entry.item.get("redirect_to")
        if redirect:
            classify("redirect", redirect, entry)
    return findings


def legacy_identifiers(legacy_root: Path | str) -> frozenset[str]:
    """Every identifier defined in a corpus, including aliases.

    Used to supply ``pending_external_ids`` while the corpus is being migrated
    domain by domain.
    """
    loaded = load_corpus(Path(legacy_root))
    known = {entry.id for entry in loaded.items if entry.id}
    for entry in loaded.items:
        known.update(entry.item.get("aliases", []) or [])
    return frozenset(known)


def _check_required_fields(loaded: LoadedCorpus, strict_layout: bool) -> list[Finding]:
    findings: list[Finding] = []
    for entry in loaded.items:
        item = entry.item
        if "redirect_to" in item and "status" not in item:
            continue  # legacy alias stub

        status = item.get("status")
        if status is None and not strict_layout:
            continue
        if status not in VALID_STATUSES:
            findings.append(
                Finding(
                    "INVALID_STATUS",
                    Severity.ERROR,
                    f"status {status!r} is not one of {sorted(VALID_STATUSES)}",
                    source=entry.source,
                    item_id=entry.id,
                )
            )
            continue

        for name in _required_fields_for(status):
            if name not in item:
                findings.append(
                    Finding(
                        "MISSING_FIELD",
                        Severity.ERROR,
                        f"status {status} requires '{name}'",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )

        if item.get("class") not in VALID_CLASSES and "class" in item:
            findings.append(
                Finding(
                    "INVALID_CLASS",
                    Severity.ERROR,
                    f"class {item.get('class')!r} is not one of {sorted(VALID_CLASSES)}",
                    source=entry.source,
                    item_id=entry.id,
                )
            )

        if status == DEPRECATED:
            continue

        scenario = item.get("scenario")
        if isinstance(scenario, dict) and not SCENARIO_KEYS.issubset(scenario):
            findings.append(
                Finding(
                    "SCENARIO_SHAPE",
                    Severity.ERROR,
                    f"scenario needs {sorted(SCENARIO_KEYS)}, has {sorted(scenario)}",
                    source=entry.source,
                    item_id=entry.id,
                )
            )

        effects = item.get("effects")
        if effects is not None and strict_layout:
            if not isinstance(effects, dict) or set(effects) != set(EFFECT_BUCKETS):
                findings.append(
                    Finding(
                        "EFFECTS_SHAPE",
                        Severity.ERROR,
                        f"effects must be an object with exactly {list(EFFECT_BUCKETS)}",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )

        if _rank(status) >= _rank("IMPLEMENTATION_REVIEW"):
            alternatives = item.get("alternatives") or []
            if len(alternatives) < MIN_ALTERNATIVES:
                findings.append(
                    Finding(
                        "TOO_FEW_ALTERNATIVES",
                        Severity.ERROR,
                        f"status {status} requires at least {MIN_ALTERNATIVES} "
                        f"alternative phrasings, found {len(alternatives)}",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )

        if _rank(status) >= _rank("DOMAIN_REVIEW"):
            perspectives = item.get("perspectives") or {}
            missing = [k for k in PERSPECTIVE_KEYS if k not in perspectives]
            if missing:
                findings.append(
                    Finding(
                        "MISSING_PERSPECTIVES",
                        Severity.ERROR,
                        f"perspectives missing {missing}; a perspective may be "
                        "NOT_APPLICABLE but may not be omitted",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )

        if status == "APPROVED":
            for name in ("domain_reviewed_by", "domain_reviewed_at"):
                if not item.get(name):
                    findings.append(
                        Finding(
                            "UNREVIEWED_APPROVAL",
                            Severity.ERROR,
                            f"APPROVED requires a non-empty '{name}'",
                            source=entry.source,
                            item_id=entry.id,
                        )
                    )
    return findings


def _rank(status: str | None) -> int:
    try:
        return STATUS_ORDER.index(status or "")
    except ValueError:
        return -1


def _check_anchors(loaded: LoadedCorpus, repo_root: Path) -> list[Finding]:
    """Resolve declared anchors against the repository.

    Paths are resolved from an explicit ``repo_root``. An earlier ad hoc script
    derived the root with ``Path(".").parent``, which is ``.``, and reported
    forty phantom missing anchors. ``test_broken_anchor_is_detected`` pins the
    behaviour so that mistake cannot recur silently.
    """
    repo_root = Path(repo_root).resolve()
    findings: list[Finding] = []
    for entry in loaded.items:
        anchors = entry.item.get("anchors") or {}
        if not isinstance(anchors, dict):
            continue
        for key in ANCHOR_FILE_KEYS:
            for anchor in anchors.get(key, []) or []:
                if not (repo_root / anchor).exists():
                    findings.append(
                        Finding(
                            "MISSING_ANCHOR",
                            Severity.ERROR,
                            f"{key} anchor does not exist: {anchor}",
                            source=entry.source,
                            item_id=entry.id,
                        )
                    )
    return findings


def _check_capability_coverage(
    loaded: LoadedCorpus, catalogue: dict[str, set[str]]
) -> list[Finding]:
    """Coverage is matched per domain.

    The previous validator compared capability strings globally, so
    ``dashboard.resolution`` satisfied the Health domain's ``resolution`` and
    ``assistant.answer-contract`` satisfied Breeding's ``ai``. Two real gaps
    were reported as full coverage.
    """
    if not catalogue:
        return []

    documented: dict[str, set[str]] = {}
    findings: list[Finding] = []
    for entry in loaded.items:
        domain = entry.item.get("domain")
        capability = entry.item.get("capability")
        if not domain or not capability:
            continue
        documented.setdefault(domain, set()).add(capability)
        if domain in catalogue and capability not in catalogue[domain]:
            findings.append(
                Finding(
                    "CAPABILITY_NOT_IN_DOMAIN",
                    Severity.WARNING,
                    f"capability {capability!r} is not listed under domain {domain!r}",
                    source=entry.source,
                    item_id=entry.id,
                )
            )

    for domain, capabilities in sorted(catalogue.items()):
        if domain not in documented:
            continue  # domain not yet authored; not a gap in what exists
        for missing in sorted(capabilities - documented[domain]):
            findings.append(
                Finding(
                    "UNDOCUMENTED_CAPABILITY",
                    Severity.ERROR,
                    f"domain {domain!r} has no item for capability {missing!r}",
                )
            )
    return findings


def _check_knowledge_provenance(loaded: LoadedCorpus) -> list[Finding]:
    findings: list[Finding] = []
    for entry in loaded.items:
        item = entry.item
        if item.get("class") != CLASS_KNOWLEDGE:
            continue
        if not item.get("clinical_safety"):
            findings.append(
                Finding(
                    "MISSING_CLINICAL_SAFETY",
                    Severity.ERROR,
                    "every curated dairy-knowledge item needs a clinical_safety statement",
                    source=entry.source,
                    item_id=entry.id,
                )
            )
        if _rank(item.get("status")) < _rank("DOMAIN_REVIEW"):
            continue
        for name in KNOWLEDGE_PROVENANCE_FIELDS:
            if not item.get(name):
                findings.append(
                    Finding(
                        "MISSING_PROVENANCE",
                        Severity.ERROR,
                        f"status {item.get('status')} requires '{name}'",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )
        text = _rendered_text(item)
        if CLINICAL_FIGURE.search(text):
            jurisdictions = item.get("jurisdiction") or []
            if not item.get("sources"):
                findings.append(
                    Finding(
                        "UNSOURCED_CLINICAL_FIGURE",
                        Severity.ERROR,
                        "item states a dose, interval or duration but cites no source",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )
            if list(jurisdictions) == ["GENERAL"]:
                findings.append(
                    Finding(
                        "UNSCOPED_CLINICAL_FIGURE",
                        Severity.ERROR,
                        "a clinical figure may not be published with jurisdiction GENERAL",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )
    return findings


def _check_text_rules(loaded: LoadedCorpus) -> list[Finding]:
    findings: list[Finding] = []
    for entry in loaded.items:
        text = _rendered_text(entry.item)

        if SIMULATOR_MENTION.search(text):
            findings.append(
                Finding(
                    "SIMULATOR_REFERENCE",
                    Severity.ERROR,
                    "the promoted source has no Simulator, so the corpus must not teach one",
                    source=entry.source,
                    item_id=entry.id,
                )
            )

        for token in set(IDENTIFIER_SHAPED.findall(text)):
            if not RESERVED_EXAMPLE_ID.match(token):
                findings.append(
                    Finding(
                        "NON_RESERVED_EXAMPLE_ID",
                        Severity.ERROR,
                        f"example identifier {token!r} is outside the reserved "
                        "EX- namespace and may be a real farm identifier",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )

        for pattern in TERMINOLOGY_VARIANTS:
            match = pattern.search(text)
            if match:
                findings.append(
                    Finding(
                        "TERMINOLOGY_VARIANT",
                        Severity.ERROR,
                        f"{match.group(0)!r} is not a DairyOS term. Passport "
                        f"categories are {list(PASSPORT_CATEGORIES)}; herd totals "
                        f"are {list(HERD_TOTAL_LABELS)}",
                        source=entry.source,
                        item_id=entry.id,
                    )
                )

    return findings


def _check_manifest(loaded: LoadedCorpus, corpus_root: Path) -> list[Finding]:
    manifest = loaded.manifest
    if manifest is None:
        return [
            Finding(
                "MANIFEST_MISSING",
                Severity.ERROR,
                "corpus has no manifest.json",
                source=str(corpus_root),
            )
        ]

    findings: list[Finding] = []
    declared = {entry.get("path"): entry for entry in manifest.get("files", []) or []}
    corpus_root = Path(corpus_root)

    for path in sorted(corpus_root.rglob("*.json")):
        rel = path.relative_to(corpus_root).as_posix()
        if rel in {"manifest.json", "capability_catalog.json"}:
            continue
        entry = declared.get(rel)
        if entry is None:
            findings.append(
                Finding("FILE_NOT_IN_MANIFEST", Severity.ERROR, "not declared", source=rel)
            )
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if entry.get("sha256") and entry["sha256"].lower() != digest:
            findings.append(
                Finding(
                    "MANIFEST_HASH_MISMATCH",
                    Severity.ERROR,
                    f"declared {entry['sha256']}, actual {digest}",
                    source=rel,
                )
            )

    servable = manifest.get("servable_statuses")
    if servable is not None and set(servable) != set(SERVABLE_STATUSES):
        findings.append(
            Finding(
                "SERVABLE_STATUSES",
                Severity.ERROR,
                f"servable_statuses must be {sorted(SERVABLE_STATUSES)}, got {servable}",
                source="manifest.json",
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate_corpus(
    corpus_root: Path | str,
    repo_root: Path | str,
    *,
    strict_layout: bool = True,
    check_manifest: bool = True,
    pending_external_ids: Iterable[str] | None = None,
) -> list[Finding]:
    """Validate a knowledge corpus and return every finding.

    ``strict_layout`` enforces the flat, non-inheriting layout ratified for the
    new corpus. It is turned off when validating the legacy ``docs/training``
    tree, whose shape predates that decision: the structural rules would then
    drown out the defects the legacy run exists to surface.
    """
    corpus_root = Path(corpus_root)
    repo_root = Path(repo_root)

    loaded = load_corpus(corpus_root)
    findings: list[Finding] = list(loaded.load_findings)
    if not loaded.items and not loaded.files:
        return findings

    findings += _check_structure(loaded, strict_layout)
    findings += _check_identifiers(loaded)
    findings += _check_cross_links(loaded, frozenset(pending_external_ids or ()))
    findings += _check_required_fields(loaded, strict_layout)
    findings += _check_anchors(loaded, repo_root)
    findings += _check_capability_coverage(loaded, _load_catalogue(corpus_root, repo_root))
    findings += _check_knowledge_provenance(loaded)
    findings += _check_text_rules(loaded)
    if check_manifest:
        findings += _check_manifest(loaded, corpus_root)

    return findings


def errors(findings: Iterable[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity is Severity.ERROR]


def codes(findings: Iterable[Finding]) -> set[str]:
    return {f.code for f in findings}


def format_report(findings: Sequence[Finding]) -> str:  # pragma: no cover
    if not findings:
        return "corpus validation: 0 findings"
    lines = [f"corpus validation: {len(findings)} findings"]
    lines += [str(finding) for finding in findings]
    return "\n".join(lines)

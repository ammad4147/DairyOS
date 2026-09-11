"""Load and search the source-backed AI Assistant knowledge corpus.

The Assistant is deliberately local and read-only.  It does not call an
external model, read the operational database, or infer permission to write a
record.  Its answer is composed from the versioned ``docs/training`` corpus,
with implementation anchors checked against the repository when the source
checkout is available.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_REVIEW_RANK = {
    "INVENTORY": 0,
    "DRAFT": 1,
    "IMPLEMENTATION_REVIEW": 2,
    "DOMAIN_REVIEW": 3,
    "APPROVED": 4,
    "DEPRECATED": -1,
}

_ROLES = (
    "Operator",
    "Supervisor",
    "Finance",
    "Veterinary / Health",
    "Technical",
)

_TOKEN_ALIASES = {
    "litre": "liter",
    "litres": "liter",
    "l": "liter",
    "tmr": "feed",
    "ai": "insemination",
    "pd": "pregnancy",
    "vax": "vaccination",
    "ill": "sick",
    "medicine": "treatment",
    "medication": "treatment",
    "cashbook": "finance",
    "cost/l": "feed cost liter",
    "cop/l": "cop liter",
}

# The disease corpus is intentionally small and reviewable.  These aliases let
# the local retriever recognise the common ways an operator describes a sign
# without pretending that a language model or a clinical diagnosis occurred.
_CLINICAL_ALIAS_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("fever", ("fever", "high temperature", "pyrexia")),
    (
        "reduced appetite",
        (
            "reduced appetite",
            "poor appetite",
            "off feed",
            "not eating",
            "inappetence",
            "reduced intake",
        ),
    ),
    (
        "abnormal milk",
        (
            "abnormal milk",
            "clots in milk",
            "flakes in milk",
            "watery milk",
            "blood in milk",
            "flakes",
            "clots",
        ),
    ),
    (
        "udder inflammation",
        (
            "udder heat",
            "hot udder",
            "hot swollen udder",
            "udder swelling",
            "swollen udder",
            "udder pain",
            "hot swollen quarter",
            "swollen quarter",
            "quarter swelling",
            "quarter pain",
            "hot quarter",
        ),
    ),
    ("cough", ("cough", "coughing")),
    (
        "nasal discharge",
        ("nasal discharge", "runny nose", "nasal mucus", "nose discharge"),
    ),
    (
        "respiratory distress",
        (
            "laboured breathing",
            "labored breathing",
            "breathing difficulty",
            "increased respiratory effort",
            "shortness of breath",
        ),
    ),
    (
        "diarrhoea",
        (
            "diarrhea",
            "diarrhoea",
            "loose faeces",
            "loose feces",
            "loose stool",
            "scours",
        ),
    ),
    ("dehydration", ("dehydration", "dehydrated")),
    ("weakness", ("weakness", "weak", "lethargy", "lethargic")),
    (
        "recumbency",
        (
            "recumbency",
            "recumbent",
            "unable to stand",
            "cannot rise",
            "can't get up",
            "down cow",
        ),
    ),
    ("cold extremities", ("cold extremities", "cold ears")),
    (
        "reduced rumen activity",
        ("reduced rumen activity", "reduced rumen movement", "rumen slowdown"),
    ),
    (
        "depression",
        ("depression", "depressed behaviour", "depressed behavior", "depressed"),
    ),
    ("lameness", ("lameness", "lame", "altered gait", "not bearing weight")),
    ("panting", ("panting", "heavy breathing", "rapid breathing")),
    (
        "reproductive loss",
        ("abortion", "abortions", "aborted", "reproductive loss", "pregnancy loss"),
    ),
    ("jaundice", ("jaundice", "yellow mucous", "yellowing")),
    ("blisters", ("blisters", "vesicles", "mouth erosions")),
    ("poor growth", ("poor growth", "not growing", "growth retardation")),
    ("itching", ("itching", "hair loss", "scratching")),
    ("anaemia", ("anaemia", "anemia", "pale mucous", "pale gums")),
)

# Operators and veterinary staff commonly use these abbreviations in notes and
# questions.  They are query aliases only; the returned record always uses the
# full, source-backed disease name.
_CLINICAL_DISEASE_ALIASES = {
    "disease.brd": ("brd",),
    "disease.bvd": ("bvd",),
    "disease.ibr": ("ibr",),
    "disease.fmd": ("fmd",),
}

_VECTOR_DIMENSIONS = 384

_STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "dairyos",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
    "with",
}


def _repo_root() -> Path:
    # ``src/dairyos/assistant`` -> repository root in a source checkout.
    return Path(__file__).resolve().parents[3]


def knowledge_root() -> Path:
    configured = os.environ.get("DAIRYOS_KNOWLEDGE_ROOT", "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())

    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        candidates.append(Path(frozen_root) / "docs" / "training")

    repository_root = _repo_root()
    candidates.extend(
        (
            repository_root / "docs" / "training",
            Path.cwd() / "docs" / "training",
        )
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise FileNotFoundError(
        "AI Assistant knowledge corpus was not found. "
        "Expected docs/training in the packaged application or source checkout."
    )


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(part for part in (_text(item) for item in value) if part)
    if isinstance(value, dict):
        return "; ".join(
            f"{key}: {_text(item)}" for key, item in value.items() if _text(item)
        )
    return str(value).strip()


def _unique(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _text(value)
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _humanize(identifier: str) -> str:
    return (
        identifier.replace(".", " - ")
        .replace("-", " ")
        .replace("_", " ")
        .strip()
        .title()
    )


def _walk_items(
    node: Any,
    source_name: str,
    inherited_status: str | None = None,
) -> Iterable[tuple[dict[str, Any], str, str]]:
    if not isinstance(node, dict):
        return
    status = _text(node.get("status")) or inherited_status or "DRAFT"
    for item in _as_list(node.get("items")):
        if isinstance(item, dict) and _text(item.get("id")):
            yield item, source_name, status.upper()
            yield from _walk_items(item, source_name, status)
    for child in _as_list(node.get("domains")):
        yield from _walk_items(child, source_name, status)


def _merge_values(left: Any, right: Any) -> Any:
    if isinstance(left, list) or isinstance(right, list):
        return _unique(_as_list(left) + _as_list(right))
    if isinstance(left, dict) and isinstance(right, dict):
        merged = dict(left)
        for key, value in right.items():
            if key in merged:
                merged[key] = _merge_values(merged[key], value)
            else:
                merged[key] = value
        return merged
    if right not in (None, "", []):
        return right
    return left


def _merge_records(
    records: Iterable[tuple[dict[str, Any], str, str]],
) -> tuple[dict[str, tuple[dict[str, Any], list[str], str]], int]:
    merged: dict[str, tuple[dict[str, Any], list[str], str]] = {}
    duplicate_count = 0
    for raw, source_name, inherited_status in records:
        item_id = _text(raw.get("id"))
        if not item_id:
            continue
        existing = merged.get(item_id)
        if existing is None:
            merged[item_id] = (dict(raw), [source_name], inherited_status)
            continue
        duplicate_count += 1
        previous, sources, previous_status = existing
        for key, value in raw.items():
            previous[key] = _merge_values(previous.get(key), value)
        sources.append(source_name)
        status_candidates = [
            previous_status,
            inherited_status,
            _text(raw.get("status")),
        ]
        status_candidates = [item.upper() for item in status_candidates if item]
        safest = min(status_candidates, key=lambda item: _REVIEW_RANK.get(item, 0))
        merged[item_id] = (previous, _unique(sources), safest)
    return merged, duplicate_count


def _disease_records(root: Path) -> Iterable[tuple[dict[str, Any], str, str]]:
    path = root / "disease-reference-catalog.json"
    if not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return
    for disease in _as_list(payload.get("items")):
        if not isinstance(disease, dict) or not _text(disease.get("name")):
            continue
        name = _text(disease["name"])
        disease_id = (
            _text(disease.get("id"))
            or f"disease.{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')}"
        )
        diagnostic = _as_list(disease.get("diagnostic_path"))
        recognition = _as_list(disease.get("recognition"))
        urgent = _as_list(disease.get("urgent"))
        prevention = _as_list(disease.get("prevention"))
        dairyos = _as_list(disease.get("dairyos"))
        management = _text(disease.get("management"))
        raw = {
            "id": disease_id,
            "domain": "health-and-veterinary",
            "capability": "disease-reference",
            "title": name,
            "clinical_class": _text(disease.get("class")),
            "clinical_recognition": recognition,
            "clinical_management": management,
            "question": f"What should I know about {name} in cattle?",
            "alternatives": [
                f"what are the signs of {name}",
                f"how is {name} assessed",
                f"how should {name} be managed",
            ],
            "answer": (
                f"{name} requires observation and veterinary assessment. "
                + (
                    f"Common recognition points include {_text(recognition)}. "
                    if recognition
                    else ""
                )
                + (
                    management
                    or "Use the authorised veterinary and farm-health pathway."
                )
            ),
            "expanded_explanation": (
                f"Recognition: {_text(recognition) or 'not specified in the reference entry'}. "
                f"Diagnostic path: {_text(diagnostic) or 'veterinarian-directed examination and testing'}. "
                f"Management: {management or 'follow the veterinarian-authorised plan'}. "
                f"Prevention: {_text(prevention) or 'follow the farm veterinary programme'}. "
                f"DairyOS records: {_text(dairyos) or 'health and related operational observations'}."
            ),
            "preconditions": [
                "Protect people and animal welfare first.",
                "Identify the animal and record objective signs before interpretation.",
            ],
            "steps": diagnostic
            or [
                "Record objective observations and timing in Health.",
                "Escalate to the responsible veterinarian for examination and diagnosis.",
                "Record authorised treatment, withdrawal, and follow-up facts in DairyOS.",
            ],
            "expected": "The animal receives timely professional assessment and the recorded facts remain traceable.",
            "next": "Follow the veterinarian's diagnosis and authorised treatment or prevention plan.",
            "exceptions": [
                {
                    "symptom": "Urgent or systemic deterioration",
                    "response": _text(urgent) or "Seek urgent veterinary care.",
                }
            ],
            "effects": dairyos,
            "safety": _text(payload.get("clinical_safety"))
            or "This is educational information, not a diagnosis or prescription.",
            "related": [
                "health.observation-triage",
                "health.treatment",
                "health.withdrawal",
            ],
            "sources": _as_list(disease.get("sources"))
            or ["DairyOS disease-reference-catalog.json"],
        }
        status = _text(disease.get("status")) or _text(payload.get("status")) or "DRAFT"
        yield raw, path.name, status.upper()


def _source_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.glob("*.json") if path.name != "capability_catalog.json"
    )


@lru_cache(maxsize=4)
def _repository_source_text(repository_name: str) -> str:
    """Read implementation text once for all anchor checks in a checkout."""
    source_root = Path(repository_name) / "src"
    if not source_root.is_dir():
        return ""

    source_text: list[str] = []
    for path in source_root.rglob("*.py"):
        try:
            source_text.append(path.read_text(encoding="utf-8-sig", errors="replace"))
        except OSError:
            continue
    return "\n".join(source_text)


def _load_raw() -> tuple[dict[str, tuple[dict[str, Any], list[str], str]], int, Path]:
    root = knowledge_root()
    records: list[tuple[dict[str, Any], str, str]] = []
    for path in _source_files(root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        records.extend(_walk_items(payload, path.name))
    records.extend(_disease_records(root))
    merged, duplicate_count = _merge_records(records)
    return merged, duplicate_count, root


def _anchor_validation(anchors: Any, root: Path) -> dict[str, Any]:
    if not isinstance(anchors, dict) or not anchors:
        return {"status": "NOT_APPLICABLE", "issues": []}

    repository = root.parent.parent
    issues: list[str] = []
    for key in ("components", "services", "models", "tests"):
        for anchor in _as_list(anchors.get(key)):
            target = repository / anchor
            if not target.is_file():
                issues.append(f"missing {key} anchor: {anchor}")

    joined_source = _repository_source_text(str(repository))
    for route in _as_list(anchors.get("routes")):
        route_text = _text(route)
        route_path = (
            route_text.split(maxsplit=1)[-1] if " " in route_text else route_text
        )
        route_marker = route_path.split("{", 1)[0].rstrip("/")
        if route_marker and route_marker not in joined_source:
            issues.append(f"route anchor not found in source: {route_text}")

    return {"status": "VALIDATED" if not issues else "BLOCKED", "issues": issues}


def _role_guidance(raw: dict[str, Any], domain: str) -> dict[str, str]:
    supplied = raw.get("roles")
    if isinstance(supplied, dict):
        result = {
            role: _text(supplied.get(role))
            for role in _ROLES
            if _text(supplied.get(role))
        }
        if result:
            return result
    clinical = (
        "health" in domain.lower()
        or "veter" in domain.lower()
        or raw.get("id", "").startswith("disease.")
    )
    guidance = {
        "Operator": "Follow the displayed workflow, record the actual fact once, and verify the saved result.",
        "Supervisor": "Review completeness, exceptions, attribution, and unresolved follow-up before accepting the outcome.",
        "Finance": "Reconcile monetary authority, period, quantity, settlement, and any downstream ledger effect where applicable.",
        "Veterinary / Health": "Use professional clinical authority for diagnosis, prescription, dosage, withdrawal, and urgent-care decisions; DairyOS is the evidence record.",
        "Technical": "Trace the authoritative source, API/service, projection, audit trail, and release identity before attempting a correction.",
    }
    if clinical:
        guidance["Operator"] = (
            "Capture objective signs and timing promptly, protect welfare, and escalate concerning cases without delaying care for data entry."
        )
    return guidance


def _normalise(
    raw: dict[str, Any],
    sources: list[str],
    inherited_status: str,
    root: Path,
) -> KnowledgeRecord:
    scenario = raw.get("scenario") if isinstance(raw.get("scenario"), dict) else {}
    item_id = _text(raw.get("id"))
    domain = _text(raw.get("domain")) or root.name
    capability = _text(raw.get("capability")) or item_id
    title = _text(raw.get("title")) or _text(raw.get("name")) or _humanize(item_id)
    question = _text(raw.get("question")) or f"How does DairyOS handle {title}?"
    alternatives = _unique(
        _as_list(raw.get("alternatives")) + _as_list(raw.get("questions"))
    )
    answer = _text(raw.get("answer"))
    if not answer and raw.get("redirect_to"):
        answer = f"This question is covered by the related DairyOS guidance {raw['redirect_to']}."
    expanded = (
        _text(raw.get("expanded_explanation"))
        or _text(raw.get("explanation"))
        or answer
    )
    preconditions = _unique(
        _as_list(raw.get("preconditions")) + _as_list(scenario.get("given"))
    )
    steps = _unique(_as_list(raw.get("steps")) + _as_list(scenario.get("steps")))
    expected = (
        _text(raw.get("expected_result"))
        or _text(raw.get("expected"))
        or _text(scenario.get("expected"))
    )
    next_action = (
        _text(raw.get("next_action"))
        or _text(raw.get("next"))
        or _text(scenario.get("next"))
    )
    exceptions: list[str] = []
    for exception in _as_list(raw.get("exceptions")):
        if isinstance(exception, dict):
            symptom = _text(exception.get("symptom"))
            response = _text(exception.get("response"))
            exceptions.append(f"{symptom}: {response}".strip(": "))
        else:
            exceptions.append(_text(exception))
    correction = _unique(
        _as_list(raw.get("correction_recovery")) + _as_list(raw.get("recovery"))
    )
    safety = (
        _text(raw.get("safety"))
        or "Do not use this read-only Assistant to authorise an operational write."
    )
    status = _text(raw.get("status")) or inherited_status or "DRAFT"
    anchors = raw.get("anchors") if isinstance(raw.get("anchors"), dict) else {}
    return KnowledgeRecord(
        id=item_id,
        domain=domain,
        capability=capability,
        title=title,
        question=question,
        alternatives=alternatives,
        answer=answer or "No grounded answer is available for this item.",
        expanded_explanation=expanded
        or "No expanded explanation is available for this item.",
        roles=_role_guidance(raw, domain),
        preconditions=preconditions,
        steps=steps,
        expected_result=expected
        or "Verify the result at the authoritative DairyOS surface.",
        next_action=next_action
        or "Escalate when the source record, calculation, or safety condition is unclear.",
        effects=_unique(_as_list(raw.get("effects")) + _as_list(raw.get("dairyos"))),
        exceptions=exceptions,
        correction_recovery=correction,
        safety=safety,
        related=_unique(_as_list(raw.get("related"))),
        anchors=anchors,
        anchor_validation=_anchor_validation(anchors, root),
        review_status=status.upper(),
        source_files=sources,
        source_authority=_unique(
            _as_list(raw.get("source_authority")) + _as_list(raw.get("sources"))
        )
        or sources,
        redirect_to=_text(raw.get("redirect_to")) or None,
        clinical_class=_text(raw.get("clinical_class")) or _text(raw.get("class")),
        clinical_recognition=tuple(
            _unique(
                _as_list(raw.get("clinical_recognition"))
                + _as_list(raw.get("recognition"))
            )
        ),
        clinical_management=_text(raw.get("clinical_management")),
    )


@dataclass(frozen=True)
class KnowledgeRecord:
    id: str
    domain: str
    capability: str
    title: str
    question: str
    alternatives: list[str]
    answer: str
    expanded_explanation: str
    roles: dict[str, str]
    preconditions: list[str]
    steps: list[str]
    expected_result: str
    next_action: str
    effects: list[str]
    exceptions: list[str]
    correction_recovery: list[str]
    safety: str
    related: list[str]
    anchors: dict[str, Any]
    anchor_validation: dict[str, Any]
    review_status: str
    source_files: list[str]
    source_authority: list[str]
    redirect_to: str | None = None
    clinical_class: str = ""
    clinical_recognition: tuple[str, ...] = ()
    clinical_management: str = ""

    def compact(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "capability": self.capability,
            "question": self.question,
            "review_status": self.review_status,
            "anchor_validation": self.anchor_validation["status"],
        }


@lru_cache(maxsize=1)
def _records() -> tuple[dict[str, KnowledgeRecord], int, Path]:
    merged, duplicate_count, root = _load_raw()
    return (
        {
            item_id: _normalise(raw, sources, status, root)
            for item_id, (raw, sources, status) in merged.items()
        },
        duplicate_count,
        root,
    )


def _tokens(value: str) -> list[str]:
    lowered = value.lower()
    lowered = re.sub(r"\bcost\s*/\s*l\b", "feed cost liter", lowered)
    lowered = re.sub(r"\bcop\s*/\s*l\b", "cop liter", lowered)
    tokens = re.findall(r"[a-z0-9]+", lowered)
    return [
        _TOKEN_ALIASES.get(token, token) for token in tokens if token not in _STOP_WORDS
    ]


def _clinical_signals(value: str) -> set[str]:
    """Return conservative, human-readable sign signals for local ranking."""
    normalized = re.sub(r"\s+", " ", str(value or "").lower()).strip()
    return {
        canonical
        for canonical, aliases in _CLINICAL_ALIAS_GROUPS
        if any(re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in aliases)
    }


def _direct_title_match(
    question: str, title: str, record_id: str = ""
) -> bool:
    """Return whether the question names the condition, not just a sign."""
    normalized_question = re.sub(r"\s+", " ", question.lower()).strip()
    title_phrases = [re.split(r"\s*\(", title, maxsplit=1)[0]]
    title_phrases.extend(re.findall(r"\(([^)]+)\)", title))
    title_phrases.extend(_CLINICAL_DISEASE_ALIASES.get(record_id, ()))
    for phrase in title_phrases:
        normalized_phrase = re.sub(r"\s+", " ", phrase.lower()).strip()
        if normalized_phrase and re.search(
            rf"\b{re.escape(normalized_phrase)}\b", normalized_question
        ):
            return True
    return False


def _clinical_context_score(
    record: KnowledgeRecord, question: str, query_signals: set[str]
) -> float:
    """Prefer a clinically coherent differential when signs are underspecified."""
    context = question.lower()
    disease_class = record.clinical_class.lower()
    score = 0.0

    respiratory_signals = {"cough", "nasal discharge", "respiratory distress"}
    if query_signals & respiratory_signals:
        score += 6.0 if "respiratory" in disease_class else -1.0
    if {"abnormal milk", "udder inflammation"} & query_signals:
        score += 6.0 if "udder" in disease_class else -1.0
    if "panting" in query_signals:
        score += 6.0 if "environmental" in disease_class else -1.0
    if {"diarrhoea", "dehydration"} <= query_signals and "calf" in context:
        score += 6.0 if "neonatal" in disease_class else -1.0
    if {"fever", "reduced appetite"} <= query_signals and (
        "metabolic" in disease_class or "postpartum" in disease_class
    ):
        score += 3.0

    postpartum_context = any(
        phrase in context
        for phrase in ("after calving", "postpartum", "fresh cow", "just calved")
    )
    if postpartum_context and {"weakness", "recumbency"} & query_signals:
        if "metabolic" in disease_class or "postpartum" in disease_class:
            score += 6.0
        if "neonatal" in disease_class:
            score -= 4.0
    if "calf" in context and "neonatal" in disease_class:
        score += 5.0
    return score


def _record_text(record: KnowledgeRecord) -> str:
    return " ".join(
        (
            record.title,
            record.question,
            " ".join(record.alternatives),
            record.answer,
            record.expanded_explanation,
            record.domain,
            record.capability,
            " ".join(record.effects),
        )
    ).lower()


def _vector(value: str, dimensions: int) -> tuple[tuple[float, ...], float]:
    """Return a deterministic feature-hashed embedding and its norm.

    The Assistant must work without a cloud model, a native vector database,
    or a user-supplied API key. Feature hashing gives the packaged corpus a
    stable local vector representation while keeping the index small and
    reproducible across restarts and machines.
    """
    values = [0.0] * dimensions
    for token in _tokens(value):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        position = int.from_bytes(digest, byteorder="big") % dimensions
        values[position] += 1.0
    norm = math.sqrt(sum(value * value for value in values))
    return tuple(values), norm


@dataclass(frozen=True)
class VectorMatch:
    record: KnowledgeRecord
    similarity: float
    overlap_count: int


class LocalVectorIndex:
    """Embeddable in-memory vector index over the packaged knowledge corpus."""

    def __init__(
        self,
        records: Iterable[KnowledgeRecord],
        dimensions: int = _VECTOR_DIMENSIONS,
    ) -> None:
        if dimensions < 32:
            raise ValueError("LocalVectorIndex requires at least 32 dimensions.")
        self.dimensions = dimensions
        self._entries = tuple(
            (
                record,
                set(_tokens(_record_text(record))),
                *_vector(_record_text(record), dimensions),
            )
            for record in records
            if record.review_status != "DEPRECATED"
        )

    def search(self, question: str, limit: int = 6) -> list[VectorMatch]:
        query_tokens = set(_tokens(question.strip()))
        query_vector, query_norm = _vector(question, self.dimensions)
        if not query_tokens or query_norm == 0.0:
            return []

        ranked: list[VectorMatch] = []
        for record, record_tokens, record_vector, record_norm in self._entries:
            overlap_count = len(query_tokens & record_tokens)
            if not overlap_count:
                continue
            if (
                len(query_tokens) >= 2
                and overlap_count < 2
                and question.lower() not in record.question.lower()
                and question.lower() not in record.title.lower()
            ):
                continue
            similarity = sum(
                left * right for left, right in zip(query_vector, record_vector)
            ) / (query_norm * record_norm)
            if similarity <= 0.0:
                continue
            ranked.append(VectorMatch(record, similarity, overlap_count))

        ranked.sort(
            key=lambda match: (
                -match.similarity,
                -match.overlap_count,
                match.record.title.lower(),
                match.record.id,
            )
        )
        return ranked[:limit]


class GroundedAssistant:
    """Question-first local Assistant over the normalized source corpus."""

    def __init__(self) -> None:
        self._items, self._duplicate_count, self._root = _records()
        self._index = LocalVectorIndex(self._items.values())

    @property
    def records(self) -> dict[str, KnowledgeRecord]:
        return self._items

    def search(self, question: str, limit: int = 6) -> list[KnowledgeRecord]:
        query = question.strip()
        query_tokens = set(_tokens(query))
        if not query_tokens:
            return []
        ranked: list[tuple[float, KnowledgeRecord]] = []
        for match in self._index.search(query, limit=max(limit * 8, 64)):
            record = match.record
            score = float(match.overlap_count) + match.similarity
            if query.lower() in record.question.lower():
                score += 12
            if query.lower() in record.title.lower():
                score += 10
            title_overlap = query_tokens & set(_tokens(record.title))
            score += len(title_overlap) * 4
            if record.id.startswith("disease.") and any(
                token in query_tokens
                for token in (
                    "sign",
                    "symptom",
                    "diagnos",
                    "disease",
                    "treat",
                    "urgent",
                )
            ):
                score += 3
            ranked.append((score, record))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].title.lower(), pair[1].id))
        return [record for _score, record in ranked[:limit]]

    def search_health(self, question: str, limit: int = 5) -> list[KnowledgeRecord]:
        """Rank disease entries by explicit signs and direct disease names.

        The general vector index remains the corpus-wide retriever.  Clinical
        differentials need one extra guard: a shared generic word such as
        ``reduced`` or ``milk`` must not promote an unrelated condition.  This
        structured pass is deterministic, inspectable, and only returns
        disease-reference entries with a direct sign or title match.
        """
        cleaned = question.strip()
        query_signals = _clinical_signals(cleaned)
        named_records = [
            record
            for record in self._items.values()
            if record.id.startswith("disease.")
            and record.review_status != "DEPRECATED"
            and _direct_title_match(cleaned, record.title, record.id)
        ]
        if named_records:
            named_signals = set().union(
                *(_clinical_signals(record.title) for record in named_records)
            )
            if not query_signals - named_signals:
                return named_records[: max(int(limit), 1)]

        context = re.sub(r"\s+", " ", cleaned.lower()).strip()
        calf_context = bool(
            re.search(r"\b(calf|calves|neonatal|newborn|youngstock)\b", context)
        )
        adult_context = bool(
            re.search(
                r"\b(cow|cows|heifer|heifers|lactating|adult cattle|postpartum|calving)\b",
                context,
            )
        )
        heat_context = bool(
            re.search(
                r"\b(heat stress|hot weather|heat wave|temperature-humidity|shade|ventilation)\b",
                context,
            )
        )
        ranked: list[tuple[float, KnowledgeRecord]] = []
        for record in self._items.values():
            if not record.id.startswith("disease."):
                continue
            if record.review_status == "DEPRECATED":
                continue
            direct_title_match = _direct_title_match(
                cleaned, record.title, record.id
            )
            disease_class = record.clinical_class.lower()
            if (
                not direct_title_match
                and "neonatal" in disease_class
                and adult_context
                and not calf_context
            ):
                continue
            if (
                not direct_title_match
                and "environmental" in disease_class
                and "panting" not in query_signals
                and not heat_context
            ):
                continue
            record_signals: set[str] = set()
            exact_signals: set[str] = set()
            for recognition in record.clinical_recognition:
                recognition_signals = _clinical_signals(recognition)
                record_signals.update(recognition_signals)
                for canonical, aliases in _CLINICAL_ALIAS_GROUPS:
                    if canonical in query_signals and any(
                        re.search(rf"\b{re.escape(alias)}\b", recognition.lower())
                        for alias in aliases
                    ):
                        exact_signals.add(canonical)
            overlap = query_signals & record_signals
            if not overlap and not direct_title_match:
                continue
            score = len(overlap) * 8.0 + len(exact_signals) * 4.0
            score += _clinical_context_score(record, cleaned, query_signals)
            if direct_title_match:
                score += 24.0
            if exact_signals:
                score += 2.0
            ranked.append((score, record))

        ranked.sort(key=lambda pair: (-pair[0], pair[1].title.lower(), pair[1].id))
        return [record for _score, record in ranked[: max(int(limit), 1)]]

    def _intent(self, question: str, record: KnowledgeRecord) -> str:
        tokens = set(_tokens(question))
        if (
            record.id.startswith("disease.")
            or "health" in record.domain.lower()
            or "veter" in record.domain.lower()
        ):
            return "INFORMATION"
        if tokens & {
            "error",
            "failed",
            "failure",
            "missing",
            "stale",
            "orphan",
            "disappear",
            "wrong",
            "not",
            "unavailable",
        }:
            return "TROUBLESHOOTING"
        if tokens & {
            "calculate",
            "calculation",
            "cost",
            "cop",
            "total",
            "rate",
            "amount",
        }:
            return "CALCULATION"
        if tokens & {"safe", "safety", "allowed", "permission", "delete", "reset"}:
            return "SAFETY"
        if tokens & {
            "checklist",
            "steps",
            "procedure",
            "sop",
            "guide",
            "record",
            "enter",
            "how",
        }:
            return "SOP / CHECKLIST"
        return "INFORMATION"

    def answer(self, question: str, role: str = "Operator") -> dict[str, Any]:
        cleaned = question.strip()
        matches = self.search(cleaned)
        if not matches:
            lowered = cleaned.lower()
            if any(
                phrase in lowered
                for phrase in (
                    "what does dairyos do",
                    "what is dairyos",
                    "what can dairyos do",
                    "what can i do in dairyos",
                )
            ):
                return {
                    "question": cleaned,
                    "answer_type": "INFORMATION",
                    "scope": "DairyOS operational guidance",
                    "title": "DairyOS capability overview",
                    "answer": "DairyOS records and connects farm operations: animals, milk production, feed and TMR, health, breeding, inventory, equipment, workforce, Finance, COP, dashboards, backups, and recovery.",
                    "expanded_explanation": "Each operational entry is persisted through its governed authority and may propagate to related dashboards, ledgers, animal passports, alerts, reports, or calculations. DairyOS can explain procedures, calculation rules, data destinations, safety boundaries, and troubleshooting steps, but this read-only Assistant does not perform farm writes.",
                    "role": role if role in _ROLES else "Operator",
                    "role_guidance": {
                        r: "Ask about the DairyOS module, record, calculation, or problem you need to understand."
                        for r in _ROLES
                    },
                    "selected_role_guidance": "Ask for a module, record type, calculation, or symptom and I will explain the governed path.",
                    "preconditions": [
                        "Name the farm area or record you want to understand."
                    ],
                    "steps": [
                        "Ask the question in plain language.",
                        "Include a date or visible error when troubleshooting.",
                        "Follow the displayed governed procedure and verify the expected result.",
                    ],
                    "expected_result": "A capability-aware answer with the relevant data authority, downstream effects, and safety boundary.",
                    "next_actions": ["Ask about a specific module or calculation."],
                    "exceptions_recovery": [
                        "If the capability is not yet covered, the Assistant will say so and identify the missing context."
                    ],
                    "effects": [
                        "Answers are grounded in the local DairyOS knowledge corpus; no live farm records are read."
                    ],
                    "safety": "Do not use the read-only Assistant to authorise destructive actions, clinical decisions, financial commitments, or operational writes.",
                    "sources": [
                        "DairyOS capability catalog",
                        "AI Assistant knowledge corpus",
                    ],
                    "related": [],
                    "coverage": self.coverage(),
                }
            return {
                "question": cleaned,
                "answer_type": "INSUFFICIENT_COVERAGE",
                "scope": "AI Assistant",
                "title": "No grounded answer found",
                "answer": "I could not find a sufficiently grounded DairyOS knowledge item for that question.",
                "expanded_explanation": "Rephrase the question with the DairyOS area, record type, symptom, date, or calculation name. The Assistant does not invent an answer or act on live records.",
                "steps": [],
                "preconditions": [],
                "expected_result": "The question is clarified or escalated with enough context for a safe answer.",
                "next_actions": [
                    "Try a more specific question",
                    "Ask an authorised DairyOS support person",
                ],
                "exceptions_recovery": [],
                "effects": [],
                "safety": "No live data was read and no farm record was changed.",
                "sources": [],
                "related": [],
                "coverage": self.coverage(),
            }

        primary = matches[0]
        if primary.redirect_to:
            redirected = self._items.get(primary.redirect_to)
            if redirected is not None and redirected.review_status != "DEPRECATED":
                primary = redirected
        intent = self._intent(cleaned, primary)
        selected_role = role if role in _ROLES else "Operator"
        related: list[KnowledgeRecord] = []
        for related_id in primary.related:
            candidate = self._items.get(related_id)
            if candidate and candidate.id != primary.id and candidate not in related:
                related.append(candidate)
        for candidate in matches[1:]:
            if candidate not in related and candidate.id != primary.id:
                related.append(candidate)
            if len(related) >= 5:
                break

        review_note = (
            "This item is implementation-anchored but its current corpus review state is "
            f"{primary.review_status}; it is not a substitute for authorised professional or management judgement."
            if primary.review_status != "APPROVED"
            else "This item is approved in the current Assistant corpus."
        )
        return {
            "question": cleaned,
            "answer_type": intent,
            "scope": (
                "Educational health and veterinary information"
                if primary.id.startswith("disease.")
                or "health" in primary.domain.lower()
                or "veter" in primary.domain.lower()
                else "DairyOS operational guidance"
            ),
            "title": primary.title,
            "answer": primary.answer,
            "expanded_explanation": primary.expanded_explanation,
            "role": selected_role,
            "role_guidance": primary.roles,
            "selected_role_guidance": primary.roles.get(
                selected_role, primary.roles["Operator"]
            ),
            "preconditions": primary.preconditions,
            "steps": primary.steps,
            "expected_result": primary.expected_result,
            "next_actions": [primary.next_action],
            "exceptions_recovery": primary.exceptions + primary.correction_recovery,
            "effects": primary.effects,
            "safety": primary.safety,
            "review": {
                "status": primary.review_status,
                "note": review_note,
                "source_files": primary.source_files,
                "source_authority": primary.source_authority,
                "implementation_anchors": primary.anchors,
                "implementation_validation": primary.anchor_validation,
            },
            "related": [item.compact() for item in related],
            "matched_items": [item.compact() for item in matches],
            "coverage": self.coverage(),
        }

    def coverage(self) -> dict[str, Any]:
        statuses: dict[str, int] = {}
        anchor_statuses: dict[str, int] = {}
        domains: set[str] = set()
        for item in self._items.values():
            statuses[item.review_status] = statuses.get(item.review_status, 0) + 1
            status = str(item.anchor_validation.get("status") or "UNKNOWN")
            anchor_statuses[status] = anchor_statuses.get(status, 0) + 1
            domains.add(item.domain)
        return {
            "items": len(self._items),
            "duplicate_source_records_merged": self._duplicate_count,
            "domains": sorted(domains),
            "review_statuses": statuses,
            "implementation_anchor_statuses": anchor_statuses,
            "knowledge_root": self._root.name,
            "retrieval": {
                "index": "LocalVectorIndex",
                "dimensions": self._index.dimensions,
                "similarity": "cosine",
            },
            "read_only": True,
        }


def knowledge_coverage() -> dict[str, Any]:
    return GroundedAssistant().coverage()

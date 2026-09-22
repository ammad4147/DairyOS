"""Evidence packaging and deterministic answer composition.

Two jobs:

1. Build a *claim-sized evidence package* for a question: the most relevant
   records, and within each record the facts that actually bear on the
   question. The same package feeds the language model and the grounding gate,
   and it is small enough that prompt processing stays fast on CPU hardware.

2. Compose a complete, grounded answer from that package without a model.
   This is used whenever the model is absent, slow, or its draft fails the
   grounding gate. Nothing is invented here: every sentence is an approved
   summary, step, fact or escalation line from the knowledge base, so this
   path cannot fabricate, and the operator still gets a useful answer rather
   than "no answer was produced" or a single record dumped verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dairyos_assistant.retrieval import Hit
from dairyos_assistant.text import Normalised, index_terms

MAX_FACTS_PRIMARY = 5
MAX_FACTS_SECONDARY = 2


@dataclass
class EvidenceItem:
    record: dict
    facts: list[str]
    steps: list[str]
    role: str  # primary | secondary | boundary

    @property
    def id(self) -> str:
        return str(self.record.get("id"))


@dataclass
class EvidencePackage:
    items: list[EvidenceItem] = field(default_factory=list)

    @property
    def ids(self) -> list[str]:
        return [item.id for item in self.items]

    def text(self) -> str:
        """All evidence text a grounded answer may draw on."""
        parts = []
        for item in self.items:
            record = item.record
            parts.append(str(record.get("title", "")))
            parts.append(str(record.get("summary", "")))
            parts.append(str(record.get("location", "") or ""))
            parts.extend(item.steps)
            parts.extend(item.facts)
            escalate = (record.get("safety") or {}).get("escalate")
            if escalate:
                parts.append(str(escalate))
        return "\n".join(p for p in parts if p)

    def prompt_block(self) -> str:
        blocks = []
        for n, item in enumerate(self.items, 1):
            record = item.record
            lines = [f"[{n}] {record.get('title')}", f"Summary: {record.get('summary')}"]
            if record.get("location"):
                lines.append(f"Where in DairyOS: {record['location']}")
            if item.steps:
                lines.append("Steps: " + " | ".join(item.steps))
            for fact in item.facts:
                lines.append(f"- {fact}")
            escalate = (record.get("safety") or {}).get("escalate")
            if escalate:
                lines.append(f"Escalation: {escalate}")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)


def _relevance(fact: str, query_terms: set[str]) -> float:
    terms = set(index_terms(fact))
    if not terms:
        return 0.0
    return len(terms & query_terms) / (len(terms) ** 0.5)


def select_facts(record: dict, query: Normalised, limit: int) -> list[str]:
    facts = list(record.get("facts") or [])
    if len(facts) <= limit:
        return facts
    query_terms = set(query.tokens) | set(query.expansions)
    scored = [(_relevance(f, query_terms), -i, f) for i, f in enumerate(facts)]
    chosen = sorted(scored, reverse=True)[:limit]
    # Keep the author's order for readability.
    return [f for _, _, f in sorted(chosen, key=lambda item: -item[1])]


def build_package(hits: list[Hit], query: Normalised, *, max_records: int = 3) -> EvidencePackage:
    package = EvidencePackage()
    if not hits:
        return package
    top = hits[0].score or 1.0
    for index, hit in enumerate(hits):
        if len(package.items) >= max_records:
            break
        if index > 0 and hit.via == "lexical" and hit.score < 0.45 * top:
            continue
        if index > 0 and hit.via != "lexical" and len(package.items) >= 2:
            continue
        primary = index == 0
        facts = select_facts(hit.record, query, MAX_FACTS_PRIMARY if primary else MAX_FACTS_SECONDARY)
        steps = list(hit.record.get("steps") or []) if primary else []
        package.items.append(EvidenceItem(hit.record, facts, steps, "primary" if primary else "secondary"))
    return package


def _source_note(record: dict) -> str | None:
    provenance = record.get("provenance") or []
    if not provenance:
        return None
    publishers = []
    for entry in provenance:
        publisher = entry.get("publisher") if isinstance(entry, dict) else None
        if publisher and publisher not in publishers:
            publishers.append(publisher)
    if not publishers:
        return None
    return "Source: " + ", ".join(publishers[:3]) + ". General guidance; your veterinarian's advice for your herd comes first."


def compose(package: EvidencePackage, *, question_is_howto: bool = False, lead: str | None = None) -> str:
    """Write an operator-facing answer from approved text only."""
    if not package.items:
        return lead or ""
    lines: list[str] = []
    if lead:
        lines.append(lead)
        lines.append("")
    primary = package.items[0]
    record = primary.record
    lines.append(str(record.get("summary", "")).strip())
    if record.get("location"):
        lines.append(f"Where: {record['location']}.")
    if primary.steps and (question_is_howto or record.get("kind") == "HOWTO"):
        lines.append("")
        lines.append("Steps:")
        lines.extend(f"{n}. {step}" for n, step in enumerate(primary.steps, 1))
    if primary.facts:
        lines.append("")
        lines.append("Key points:")
        lines.extend(f"- {fact}" for fact in primary.facts)
    for item in package.items[1:]:
        if item.role == "boundary":
            continue
        lines.append("")
        lines.append(f"Also relevant ({item.record.get('title')}): {item.record.get('summary')}")
        for fact in item.facts[:1]:
            lines.append(f"- {fact}")
    escalations = []
    for item in package.items:
        escalate = (item.record.get("safety") or {}).get("escalate")
        if escalate and escalate not in escalations:
            escalations.append(escalate)
    if escalations:
        lines.append("")
        lines.append("When to involve the veterinarian: " + " ".join(escalations[:2]))
    note = _source_note(record)
    if note:
        lines.append("")
        lines.append(note)
    return "\n".join(lines).strip()

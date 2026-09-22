"""The grounding gate: what a generated answer is allowed to say.

A small language model asked about a withdrawal period or a sick calf will
write a confident sentence whether or not it was given the facts. The gate
compares every generated draft with the evidence package it was given and
rejects the draft when it:

* states a number that is not in the evidence or the question (doses, day
  counts, thresholds and farm figures are almost always numbers);
* claims to have consulted this farm's records;
* invents a record identifier (an animal tag, a case number);
* gives a dose, a dosing unit, or an instruction to administer a named drug
  that the evidence does not contain;
* asserts a diagnosis of the operator's animal;
* drifts away from the evidence (too few of its content words appear in it);
* echoes the prompt's scaffolding or rules back to the operator;
* is empty or unreasonably long.

The gate applies to every route that produces dairy, veterinary or DairyOS
content. A rejected draft is never repaired; the service replaces it with the
deterministic composed answer, which is built only from approved text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from dairyos_assistant.policy import REAL_IDENTIFIER
from dairyos_assistant.text import index_terms

MAX_ANSWER_CHARACTERS = 2600
MIN_EVIDENCE_OVERLAP = 0.55

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_LIST_MARKER = re.compile(r"^[ \t]*\d{1,2}[.)]\s+", re.MULTILINE)
_DOSE = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|ml|mL|cc|iu|IU|units?)\b|\b(?:mg|ml|cc)\s?/\s?kg\b|\bper (?:kg|kilogram) (?:of )?body ?weight\b",
)
_DRUG = re.compile(
    r"\b(?:oxytetracycline|penicillin|streptomycin|ceftiofur|amoxicillin|ampicillin|cloxacillin|flunixin|meloxicam|"
    r"ketoprofen|borogluconate|ivermectin|albendazole|oxytocin|dexamethasone|enrofloxacin|tylosin|gentamicin|"
    r"sulfa\w*|trimethoprim|tetracycline|cephalexin|cefquinome|marbofloxacin)\b",
    re.I,
)
_ADMINISTER = re.compile(r"\b(?:give|inject|administer|dose|drench|infuse|treat (?:her|him|it|the cow) with|use)\b", re.I)
_DIAGNOSIS = re.compile(
    r"\b(?:your cow|your animal|your calf|she|it) (?:definitely |probably |certainly )?(?:has|is suffering from|is infected with)\b"
    r"[^.]{0,30}\b(?:mastitis|ketosis|milk fever|metritis|pneumonia|brucellosis|fmd|foot.and.mouth|lsd|bvd|acidosis)\b|"
    r"\bi (?:can )?confirm (?:that )?(?:she|it|the cow|your cow)\b|\bthe diagnosis is\b",
    re.I,
)
_DATA_ACCESS = re.compile(
    r"your (?:farm'?s? )?records show|according to your (?:records|data|farm)|i (?:have )?checked your|i looked at your|"
    r"looking at your herd|in your database|i can see (?:that )?your|your herd data shows|from your farm data|"
    r"the farm records show|your milk records show|based on your farm'?s? (?:data|records)",
    re.I,
)
_SCAFFOLD = re.compile(r"REFERENCE:|EVIDENCE:|Rules you must follow|Reasoning task|\[\d+\]|The applicable fact is", re.I)
_SENTENCE_SPLIT = re.compile(r"(?:[.!?\u0964\u06d4]+|\n+)")


def _repetition_violation(text: str) -> str | None:
    """Reject decoder loops while allowing ordinary short lists and emphasis.

    Small local models can enter a loop and repeat one sentence many times.
    Such a draft may still share enough words with the evidence to pass the
    grounding overlap check, but it is not an answer an operator can use.
    Require a meaningful sentence (at least 12 characters) and three repeats;
    this avoids rejecting normal duplicated labels or short acknowledgements.
    """
    units = [re.sub(r"\s+", " ", unit).strip().casefold() for unit in _SENTENCE_SPLIT.split(text)]
    units = [unit for unit in units if len(unit) >= 12]
    counts: dict[str, int] = {}
    for unit in units:
        counts[unit] = counts.get(unit, 0) + 1
    repeated = max(counts.values(), default=0)
    if repeated >= 3:
        return f"repeated generated sentence ({repeated} times)"
    return None


@dataclass(frozen=True)
class Verdict:
    ok: bool
    violations: tuple[str, ...] = ()
    unsupported_numbers: tuple[str, ...] = ()
    overlap: float = 1.0
    checked_against: tuple[str, ...] = field(default=())

    def __bool__(self) -> bool:
        return self.ok


def _normalise_number(token: str) -> str:
    cleaned = token.replace(",", "")
    if "." in cleaned:
        cleaned = cleaned.rstrip("0").rstrip(".")
    return cleaned or "0"


def numbers_in(text: str) -> set[str]:
    without_markers = _LIST_MARKER.sub("", text or "")
    return {_normalise_number(m.group(0)) for m in _NUMBER.finditer(without_markers)}


def evidence_overlap(answer: str, evidence: str, question: str = "") -> float:
    answer_terms = set(index_terms(answer))
    if not answer_terms:
        return 0.0
    allowed = set(index_terms(evidence)) | set(index_terms(question))
    return len(answer_terms & allowed) / len(answer_terms)


def check(
    answer: str,
    evidence: str,
    *,
    question: str = "",
    record_ids: tuple[str, ...] = (),
    allow_derived_numbers: bool = False,
    min_overlap: float = MIN_EVIDENCE_OVERLAP,
) -> Verdict:
    text = (answer or "").strip()
    if not text:
        return Verdict(False, ("empty answer",), (), 0.0, record_ids)
    violations: list[str] = []
    repeated = _repetition_violation(text)
    if repeated:
        violations.append(repeated)
    if len(text) > MAX_ANSWER_CHARACTERS:
        violations.append(f"answer is {len(text)} characters, over the {MAX_ANSWER_CHARACTERS} limit")
    if not evidence.strip():
        violations.append("no evidence was supplied, so nothing can be grounded")
    if _DATA_ACCESS.search(text):
        violations.append("claims access to farm data")
    invented = [i for i in REAL_IDENTIFIER.findall(text) if i not in (question or "") and i not in evidence]
    if invented:
        violations.append(f"invented record identifiers: {sorted(set(invented))}")
    dose = _DOSE.search(text)
    if dose and dose.group(0) not in evidence and dose.group(0) not in question:
        violations.append(f"dose or dosing unit not in evidence: {dose.group(0)!r}")
    for drug in {m.group(0).lower() for m in _DRUG.finditer(text)}:
        if drug not in evidence.lower() and _ADMINISTER.search(text):
            violations.append(f"medicine instruction not in evidence: {drug}")
    if _DIAGNOSIS.search(text):
        violations.append("asserts a diagnosis of the operator's animal")
    if _SCAFFOLD.search(text):
        violations.append("echoes prompt scaffolding")
    unsupported: tuple[str, ...] = ()
    if not allow_derived_numbers:
        supported = numbers_in(evidence) | numbers_in(question)
        missing = sorted(numbers_in(text) - supported)
        if missing:
            unsupported = tuple(missing)
            violations.append(f"numbers not present in the evidence: {missing}")
    overlap = evidence_overlap(text, evidence, question)
    if overlap < min_overlap:
        violations.append(f"answer drifts from the evidence (overlap {overlap:.2f} < {min_overlap})")
    return Verdict(not violations, tuple(violations), unsupported, round(overlap, 3), record_ids)

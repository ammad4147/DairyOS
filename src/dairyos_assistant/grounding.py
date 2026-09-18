"""The grounding gate: what a generated answer is allowed to say.

A language model asked to explain a withdrawal period will produce a confident
sentence whether or not it was told the figure. On a dairy farm that sentence
can put milk carrying antibiotic residue into a tank. The gate exists so that
the Assistant's fluency is never mistaken for knowledge.

The checks here are deterministic and adversarial. They do not ask the model
whether it was faithful, because a model that fabricates a figure will also
attest to it. They compare the produced text against the retrieved evidence and
reject anything the evidence does not carry.

The strongest rule is the numeric one. Fabrication in this domain is almost
always a number: a day count, a dose, a withdrawal interval, a threshold. Any
number in the answer that does not appear in the evidence is grounds for
rejection on its own, and that single rule catches the class of error that
matters most while being impossible to argue with.

A rejected answer is not repaired and not shown. The Assistant says it does not
know, which is always a true statement and never a dangerous one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from dairyos_assistant.policy import REAL_IDENTIFIER

# Fields of a corpus item whose text counts as evidence. Metadata such as the
# reviewer name is excluded: a number in an audit field is not a fact the
# Assistant may repeat as guidance.
EVIDENCE_FIELDS = (
    "question",
    "answer",
    "explanation",
    "scenario",
    "alternatives",
    "perspectives",
    "exceptions",
    "effects",
    "correction_path",
    "title",
    "capability",
    "domain",
)

MAX_ANSWER_CHARACTERS = 2400

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_LIST_MARKER = re.compile(r"^[ \t]*\d{1,2}[.)]\s+", re.MULTILINE)

# A concrete record identifier outside the reserved fictional namespace. The
# Assistant has no records, so producing one means inventing it.
#
# Imported from the policy layer rather than restated, so the rule that decides
# what counts as a record identifier cannot say one thing when classifying a
# question and another when checking an answer.
_REAL_IDENTIFIER = REAL_IDENTIFIER

# Claims to have consulted farm data. The Assistant cannot have done so, which
# makes any of these false regardless of what follows them.
_DATA_ACCESS_CLAIMS = (
    "your farm's records",
    "your farm records",
    "your records show",
    "according to your data",
    "i checked your",
    "i looked at your",
    "looking at your herd",
    "in your database",
    "your current herd",
    "based on your farm",
    "i can see that your",
)


@dataclass(frozen=True)
class Verdict:
    """Whether an answer may be shown, and if not, precisely why."""

    ok: bool
    violations: tuple[str, ...] = ()
    unsupported_numbers: tuple[str, ...] = ()
    checked_against: tuple[str, ...] = field(default=())

    def __bool__(self) -> bool:
        return self.ok


def _normalise_number(token: str) -> str:
    """Compare numbers by value, not by typography.

    ``1,000``, ``1000`` and ``1000.0`` are the same figure, and an answer should
    not be rejected for reformatting one the evidence stated differently.
    """
    cleaned = token.replace(",", "")
    if "." in cleaned:
        cleaned = cleaned.rstrip("0").rstrip(".")
    return cleaned or "0"


def numbers_in(text: str) -> set[str]:
    """Every number in the text, ignoring list markers.

    ``1.`` and ``2)`` at the start of a line enumerate steps; they assert
    nothing and must not have to be supported by evidence.
    """
    without_markers = _LIST_MARKER.sub("", text or "")
    return {_normalise_number(m.group(0)) for m in _NUMBER.finditer(without_markers)}


def evidence_text(sources: Iterable[dict[str, Any]]) -> str:
    """Flatten the evidence to the text a claim may be grounded in."""
    parts: list[str] = []
    for item in sources:
        for name in EVIDENCE_FIELDS:
            value = item.get(name)
            if value is None:
                continue
            if isinstance(value, dict):
                parts.extend(str(v) for v in value.values() if v is not None)
            elif isinstance(value, (list, tuple)):
                parts.extend(str(v) for v in value if v is not None)
            else:
                parts.append(str(value))
    return "\n".join(parts)


def check(
    answer: str,
    sources: Sequence[dict[str, Any]],
    *,
    question: str = "",
    allow_derived_numbers: bool = False,
) -> Verdict:
    """Decide whether a generated answer may be shown.

    ``allow_derived_numbers`` is for the calculation carve-out only. When the
    operator supplies figures in the question and asks for arithmetic, the
    result is by definition a number that appears in no corpus item, so the
    numeric rule cannot apply. Every other rule still does, which is what stops
    the carve-out being used to smuggle an invented fact past the gate.
    """
    violations: list[str] = []
    text = (answer or "").strip()

    if not text:
        return Verdict(False, ("empty answer",), (), tuple(s.get("id", "") for s in sources))

    if len(text) > MAX_ANSWER_CHARACTERS:
        violations.append(
            f"answer is {len(text)} characters, over the {MAX_ANSWER_CHARACTERS} limit"
        )

    if not sources and not allow_derived_numbers:
        violations.append("no evidence was retrieved, so nothing can be grounded")

    lowered = text.lower()
    for claim in _DATA_ACCESS_CLAIMS:
        if claim in lowered:
            violations.append(f"claims access to farm data: {claim!r}")

    invented = _REAL_IDENTIFIER.findall(text)
    # An identifier the operator themselves put in the question is theirs, not
    # an invention, though the policy layer will normally have refused such a
    # question long before it reached here.
    invented = [i for i in invented if i not in (question or "")]
    if invented:
        violations.append(f"invented record identifiers: {sorted(set(invented))}")

    unsupported: tuple[str, ...] = ()
    if not allow_derived_numbers:
        supported = numbers_in(evidence_text(sources)) | numbers_in(question)
        produced = numbers_in(text)
        missing = sorted(produced - supported)
        if missing:
            unsupported = tuple(missing)
            violations.append(f"numbers not present in the evidence: {missing}")

    return Verdict(
        ok=not violations,
        violations=tuple(violations),
        unsupported_numbers=unsupported,
        checked_against=tuple(str(s.get("id", "")) for s in sources),
    )


REJECTED_TEXT = (
    "I could not give you a reliable answer to that. What I drafted was not "
    "fully supported by the approved knowledge base, so I have withheld it "
    "rather than risk telling you something incorrect."
)

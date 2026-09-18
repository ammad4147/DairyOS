"""Deterministic question policy: what the Assistant will and will not answer.

This module is the security boundary expressed as code rather than as a prompt.
It runs before retrieval and before any model is consulted, so the decision to
refuse a request for farm data cannot be argued with, reworded around, or
overridden by a claim of authority. A request to ignore these rules is itself
classified by them.

The classification is intentionally conservative. A wrongly refused question
costs the operator one redirection to the screen that holds the answer. A
wrongly answered one would mean the Assistant appearing to read farm records it
cannot read, which is the failure this whole subsystem exists to prevent.

One carve-out is deliberate and is required by the product definition: values
the operator types into the conversation are theirs to reason about. Asking the
Assistant to work out a percentage from two numbers in the question is a
calculation, not a retrieval, and is answered.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    """What the orchestration layer should do with a question."""

    ANSWER = "ANSWER"
    """Answer from approved knowledge."""

    CALCULATE = "CALCULATE"
    """Arithmetic on values the operator supplied in the question itself."""

    REFUSE_OPERATIONAL_DATA = "REFUSE_OPERATIONAL_DATA"
    """A request for this farm's records, which the Assistant cannot reach."""


@dataclass(frozen=True)
class PolicyResult:
    decision: Decision
    reason: str = ""
    signals: tuple[str, ...] = ()

    @property
    def refused(self) -> bool:
        return self.decision is Decision.REFUSE_OPERATIONAL_DATA


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

# Nouns that name operational subject matter. On their own these are innocuous:
# "how is milk recorded" is a product question. They become operational when
# combined with a possessive or a deictic time reference.
_OPERATIONAL_NOUNS = r"(?:milk|yield|litres?|liters?|production|cow|cows|animal|animals|heifer|heifers|calf|calves|bull|bulls|herd|feed|tmr|ration|revenue|income|expense|expenses|cost|cop|coml|profit|sale|sales|breeding|insemination|pregnanc\w*|calving|semen|straws?|health|case|cases|treatment|withdrawal|vaccination|stock|inventory|dashboard|alert|alerts|watchlist|farm|record|records|finance|financial|technician|technicians|supplier|customer)"

# First person possessives and subjects: the operator speaking about their farm.
_POSSESSIVE = r"\b(?:my|our|we|us|mine|ours)\b"

# Deictic time: anchored to now, which only farm data can answer.
_DEICTIC_TIME = r"\b(?:today|todays|today's|yesterday|tonight|this\s+(?:morning|afternoon|evening|week|month|season|year)|last\s+(?:night|week|month)|right\s+now|currently|at\s+the\s+moment|so\s+far)\b"

# Quantity interrogatives aimed at a stored value.
_HOW_MUCH = r"\bhow\s+(?:much|many)\b"

# Selection interrogatives: picking records out of a population.
_WHICH_RECORD = r"\bwhich\s+(?:\w+\s+){0,2}(?:cow|cows|animal|animals|heifer|heifers|calf|calves|bull|bulls|one|ones|technician|technicians|supplier|customer|lot|batch)\b"

# Imperative retrieval.
_RETRIEVE_VERB = r"\b(?:show|list|display|fetch|retrieve|pull\s+up|give\s+me|tell\s+me)\b"

# Analysis of the operator's own data.
_ANALYSE_MINE = r"\b(?:analyse|analyze|review|audit|summarise|summarize|check)\b[^.?!]{0,30}\b(?:my|our|the)\s+" + _OPERATIONAL_NOUNS

# A concrete record identifier that is not in the reserved fictional namespace.
#
# The leading lookbehind is load-bearing. Without it the pattern matches the
# "MILK-001" inside "EX-MILK-001", because a word boundary falls after the
# hyphen and the "not EX-" lookahead only guards the start of the match. The
# effect was that an operator asking about the Assistant's own worked examples
# had the question refused as a request for a record.
REAL_IDENTIFIER = re.compile(r"(?<![A-Z0-9-])(?!EX-)[A-Z]{2,4}-\d{1,5}\b")
_REAL_IDENTIFIER = REAL_IDENTIFIER

# Attempts to grant the Assistant authority it does not have. These are
# classified as operational-data requests because that is what they are asking
# for; the wrapper does not change the request.
_AUTHORITY_CLAIM = re.compile(
    r"\b(?:i\s+authoris\w+|i\s+authoriz\w+|i(?:\s+am|'m|’m)\s+the\s+(?:administrator|admin|owner|operator)|"
    r"as\s+(?:the\s+)?(?:administrator|admin|owner)|you\s+have\s+permission|i\s+give\s+you\s+permission|"
    r"ignore\s+(?:your|the|all|previous)\s+(?:instructions?|rules?|restrictions?)|"
    r"bypass\s+(?:your|the)\s+\w+|"
    r"(?:query|read|access|connect\s+to|open)\s+(?:the\s+)?(?:database|db|postgres|postgresql|farm\s+database)|"
    r"execute\s+sql|run\s+sql|"
    r"use\s+(?:the\s+)?(?:internal|operational)\s+api|call\s+the\s+\w+\s+service\s+directly|"
    r"read\s+runtime\.json|use\s+simulator\s+data)\b",
    re.IGNORECASE,
)

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("possessive+operational", re.compile(_POSSESSIVE + r"[^.?!]{0,40}?" + _OPERATIONAL_NOUNS, re.IGNORECASE)),
    ("operational+possessive", re.compile(_OPERATIONAL_NOUNS + r"[^.?!]{0,20}?" + _POSSESSIVE, re.IGNORECASE)),
    ("deictic-time+operational", re.compile(_DEICTIC_TIME + r"[^.?!]{0,40}?" + _OPERATIONAL_NOUNS, re.IGNORECASE)),
    ("operational+deictic-time", re.compile(_OPERATIONAL_NOUNS + r"[^.?!]{0,40}?" + _DEICTIC_TIME, re.IGNORECASE)),
    ("how-much+operational", re.compile(_HOW_MUCH + r"[^.?!]{0,40}?" + _OPERATIONAL_NOUNS, re.IGNORECASE)),
    ("which-record", re.compile(_WHICH_RECORD, re.IGNORECASE)),
    ("retrieve+operational", re.compile(_RETRIEVE_VERB + r"[^.?!]{0,30}?" + _OPERATIONAL_NOUNS, re.IGNORECASE)),
    ("analyse-mine", re.compile(_ANALYSE_MINE, re.IGNORECASE)),
)

# Phrasings that ask how the software works. These do not make a question safe
# on their own, but they are what a product question looks like, and they are
# recorded so a refusal can be explained.
_INSTRUCTIONAL = re.compile(
    r"\b(?:how\s+do\s+i|how\s+is\s+\w+\s+calculat|how\s+are\s+\w+\s+calculat|how\s+does\s+dairyos|"
    r"what\s+does\s+\w+\s+mean|what\s+is\s+a\b|what\s+is\s+the\s+difference|where\s+(?:do|does|is|can)\s+i|"
    r"what\s+happens\s+(?:if|when|after)|why\s+(?:is|isn't|does|doesn't)\s+\w+\s+(?:included|excluded)|"
    r"how\s+should\s+i|what\s+should\s+i\s+record|explain)\b",
    re.IGNORECASE,
)

# Arithmetic intent, for the user-supplied-values carve-out.
_ARITHMETIC_INTENT = re.compile(
    r"\b(?:calculate|work\s+out|what\s+(?:percentage|percent|%)|how\s+much\s+is|what\s+is\s+the\s+(?:drop|difference|change|increase|decrease)|"
    r"percentage\s+drop|percent\s+drop|what\s+is\s+the\s+[\w\s]{0,20}?per\s+\w+|cost\s+per\s+\w+)\b",
    re.IGNORECASE,
)

# Two or more explicit quantities in the question itself.
_QUANTITY = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:l\b|litres?|liters?|kg|kgs?|pkr|rs\.?|%|percent)?", re.IGNORECASE)


def _supplied_quantities(text: str) -> int:
    return len([m for m in _QUANTITY.finditer(text) if re.search(r"\d", m.group(0))])


def classify(question: str) -> PolicyResult:
    """Decide how a question may be handled.

    This function consults no corpus, no model and no configuration. Given the
    same text it always returns the same decision, which is what makes the
    boundary testable.
    """
    text = (question or "").strip()
    if not text:
        return PolicyResult(Decision.ANSWER, "empty question")

    signals: list[str] = []

    if _AUTHORITY_CLAIM.search(text):
        signals.append("authority-claim")

    for name, pattern in _PATTERNS:
        if pattern.search(text):
            signals.append(name)

    if _REAL_IDENTIFIER.search(text):
        signals.append("record-identifier")

    if not signals:
        return PolicyResult(Decision.ANSWER, "no operational signal")

    # The section 29 carve-out. Values the operator typed are theirs to reason
    # about, so a question that both supplies its own numbers and asks for
    # arithmetic is a calculation rather than a retrieval. An authority claim
    # or a concrete record identifier disqualifies it, because those ask the
    # Assistant to reach for something it was not given.
    disqualifying = {"authority-claim", "record-identifier"}
    if (
        _ARITHMETIC_INTENT.search(text)
        and _supplied_quantities(text) >= 2
        and not disqualifying.intersection(signals)
    ):
        return PolicyResult(
            Decision.CALCULATE,
            "the question supplies its own values and asks for arithmetic",
            tuple(signals),
        )

    return PolicyResult(
        Decision.REFUSE_OPERATIONAL_DATA,
        "the question asks about this farm's records",
        tuple(signals),
    )


def is_instructional(question: str) -> bool:
    """Whether a question is phrased as a product question.

    Used only to shape the wording of a refusal, never to override one.
    """
    return bool(_INSTRUCTIONAL.search(question or ""))


REFUSAL_TEXT = (
    "I do not have access to your farm's records, so I cannot answer that from "
    "your data. I can explain where DairyOS shows it, how DairyOS calculates "
    "it, and what the figures mean."
)

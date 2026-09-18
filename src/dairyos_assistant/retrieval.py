"""Deterministic lexical retrieval over the approved knowledge corpus.

The design is deliberately unfashionable. Scoring is BM25 over a few weighted
text fields, computed from the corpus itself with no model, no embedding and no
extra dependency in the frozen executable. For a corpus of roughly a hundred
short, heavily curated items that is sufficient, and it buys three properties
that matter more here than recall at the margin:

* It is deterministic. The same question returns the same items in the same
  order, which means retrieval behaviour can be pinned by tests rather than
  sampled.
* It is explainable. Every hit carries the terms that matched, so an operator
  or a reviewer can see why an item was chosen.
* It adds nothing to the Assistant's dependency surface, which is the whole
  basis of the isolation argument.

Embeddings can be added later behind the same interface if measured recall
proves inadequate. That is a decision for evidence, not for taste.

**Servability.** Only items whose status is in the corpus manifest's
``servable_statuses`` are indexed, and that list is ``["APPROVED"]``. A corpus
whose items have not been reviewed therefore serves nothing at all, which is
the intended behaviour of the review gate rather than a defect.

Two things widen that, both deliberate and both visible. A caller may pass
``servable_statuses`` explicitly, and a pre-release build widens it via
``release.PRE_RELEASE``. In either case every item served below ``APPROVED``
is marked ``unreviewed`` on the hit itself, so the distinction cannot be lost
by a downstream layer that forgets to check the build flag.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from dairyos_assistant.corpus.validation import (
    DEPRECATED,
    SERVABLE_STATUSES,
    load_corpus,
)
from dairyos_assistant.release import PRE_RELEASE, PRE_RELEASE_STATUSES


# Field weights. Question and alternative phrasings carry the most signal
# because they are written in the operator's own words; body text carries the
# least because a common term appearing in a long explanation says little.
FIELD_WEIGHTS: dict[str, float] = {
    "question": 3.0,
    "alternatives": 3.0,
    "title": 2.0,
    "capability": 2.0,
    "domain": 1.0,
    "answer": 1.0,
    "explanation": 0.5,
}

# BM25 parameters. Standard values; k1 controls term-frequency saturation and b
# controls length normalisation.
K1 = 1.2
B = 0.6

# A hit below this score is treated as no match, so the Assistant says it has
# no approved knowledge rather than returning its least-bad guess.
DEFAULT_MIN_SCORE = 1.0
DEFAULT_LIMIT = 5

_TOKEN = re.compile(r"[a-z0-9]+")


def resolve_servable_statuses(
    manifest: dict,
    explicit: Iterable[str] | None = None,
    *,
    pre_release: bool = PRE_RELEASE,
) -> frozenset[str]:
    """Decide which statuses this index will serve, in precedence order.

    An explicit argument wins, because a caller that names its threshold has
    said what it means. Otherwise a pre-release build widens the manifest's
    threshold, and a certified build uses the manifest unchanged.

    Kept as a free function so both branches can be asserted directly, rather
    than only through whatever the current build constant happens to be.
    """
    if explicit is not None:
        return frozenset(explicit)
    declared = frozenset(manifest.get("servable_statuses") or SERVABLE_STATUSES)
    if pre_release:
        return declared | frozenset(PRE_RELEASE_STATUSES)
    return declared

# Words carrying no discriminating power in a corpus that is entirely about
# one product. Deliberately short: over-aggressive stopping loses real signal
# in questions as terse as operators actually type them.
_STOPWORDS = frozenset(
    """
    a an and are as at be by do does for from how i in is it its of on or
    should that the their them there these this to was what when where which
    who why will with you your
    """.split()
)


def tokenise(text: str) -> list[str]:
    return [t for t in _TOKEN.findall((text or "").lower()) if t not in _STOPWORDS]


@dataclass(frozen=True)
class Hit:
    knowledge_id: str
    title: str
    domain: str
    capability: str
    item_class: str
    status: str
    score: float
    matched_terms: tuple[str, ...]
    unreviewed: bool
    item: dict

    @property
    def answer(self) -> str:
        return str(self.item.get("answer", ""))


@dataclass
class KnowledgeIndex:
    """An in-memory lexical index over the servable items of one corpus."""

    corpus_version: str = ""
    dairyos_source_authority: str = ""
    servable_statuses: frozenset[str] = frozenset(SERVABLE_STATUSES)
    documents: list[dict] = field(default_factory=list)
    _postings: dict[str, dict[int, float]] = field(default_factory=dict)
    _lengths: list[float] = field(default_factory=list)
    _avg_length: float = 0.0
    _skipped_by_status: dict[str, int] = field(default_factory=dict)

    # -- construction -------------------------------------------------------

    @classmethod
    def load(
        cls,
        corpus_root: Path | str,
        *,
        servable_statuses: Iterable[str] | None = None,
    ) -> "KnowledgeIndex":
        corpus_root = Path(corpus_root)
        loaded = load_corpus(corpus_root)

        manifest_path = corpus_root / "manifest.json"
        manifest: dict = {}
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                manifest = {}

        allowed = resolve_servable_statuses(manifest, servable_statuses)

        index = cls(
            corpus_version=str(manifest.get("corpus_version", "")),
            dairyos_source_authority=str(manifest.get("dairyos_source_authority", "")),
            servable_statuses=allowed,
        )

        for entry in loaded.items:
            item = entry.item
            status = item.get("status")
            # A deprecated item is never served, whatever the threshold says:
            # it exists to redirect, not to answer.
            if status == DEPRECATED or "redirect_to" in item:
                index._skipped_by_status[DEPRECATED] = index._skipped_by_status.get(DEPRECATED, 0) + 1
                continue
            if status not in allowed:
                index._skipped_by_status[str(status)] = index._skipped_by_status.get(str(status), 0) + 1
                continue
            index.documents.append(item)

        index._build()
        return index

    def _build(self) -> None:
        self._postings = {}
        self._lengths = []
        for position, item in enumerate(self.documents):
            weighted: dict[str, float] = {}
            length = 0.0
            for field_name, weight in FIELD_WEIGHTS.items():
                value = item.get(field_name)
                if value is None:
                    continue
                text = " ".join(value) if isinstance(value, list) else str(value)
                for token in tokenise(text):
                    weighted[token] = weighted.get(token, 0.0) + weight
                    length += weight
            self._lengths.append(length)
            for token, tf in weighted.items():
                self._postings.setdefault(token, {})[position] = tf
        self._avg_length = (sum(self._lengths) / len(self._lengths)) if self._lengths else 0.0

    # -- query --------------------------------------------------------------

    def _idf(self, token: str) -> float:
        n = len(self.documents)
        df = len(self._postings.get(token, ()))
        if df == 0:
            return 0.0
        # BM25 idf, floored at zero so a term present in every document cannot
        # push a score negative.
        return max(0.0, math.log(1.0 + (n - df + 0.5) / (df + 0.5)))

    def search(
        self,
        query: str,
        *,
        limit: int = DEFAULT_LIMIT,
        min_score: float = DEFAULT_MIN_SCORE,
        min_matched_terms: int | None = None,
    ) -> list[Hit]:
        """Rank servable items against a query.

        Two independent gates must both be cleared. ``min_score`` rejects a
        weak match, and ``min_matched_terms`` rejects a match that rests on too
        few of the query's own terms.

        The second gate exists because a single shared word is not evidence.
        "What is the capital of France?" overlaps a finance item on the word
        "capital", which is a real lexical match and an entirely wrong answer.
        Requiring two distinct query terms to match, where the query offers
        two, costs nothing on real questions and removes that class of
        false positive.
        """
        terms = tokenise(query)
        if not terms or not self.documents:
            return []

        required_terms = (
            min(2, len(terms)) if min_matched_terms is None else min_matched_terms
        )

        scores: dict[int, float] = {}
        matched: dict[int, set[str]] = {}

        for token in terms:
            postings = self._postings.get(token)
            if not postings:
                continue
            idf = self._idf(token)
            if idf <= 0.0:
                continue
            for position, tf in postings.items():
                length = self._lengths[position] or 1.0
                norm = 1.0 - B + B * (length / (self._avg_length or 1.0))
                contribution = idf * (tf * (K1 + 1.0)) / (tf + K1 * norm)
                scores[position] = scores.get(position, 0.0) + contribution
                matched.setdefault(position, set()).add(token)

        ranked = sorted(
            (
                p
                for p, s in scores.items()
                if s >= min_score and len(matched.get(p, ())) >= required_terms
            ),
            key=lambda p: (-scores[p], self.documents[p].get("id", "")),
        )

        hits: list[Hit] = []
        for position in ranked[:limit]:
            item = self.documents[position]
            status = str(item.get("status", ""))
            hits.append(
                Hit(
                    knowledge_id=str(item.get("id", "")),
                    title=str(item.get("title", "")),
                    domain=str(item.get("domain", "")),
                    capability=str(item.get("capability", "")),
                    item_class=str(item.get("class", "")),
                    status=status,
                    score=round(scores[position], 4),
                    matched_terms=tuple(sorted(matched.get(position, ()))),
                    unreviewed=status not in SERVABLE_STATUSES,
                    item=item,
                )
            )
        return hits

    # -- diagnostics --------------------------------------------------------

    @property
    def servable_count(self) -> int:
        return len(self.documents)

    def status_report(self) -> dict:
        """Why the index holds what it holds.

        Reported by the diagnostics surface so that an Assistant serving
        nothing is legible as an unreviewed corpus rather than as a fault.
        """
        return {
            "corpus_version": self.corpus_version,
            "dairyos_source_authority": self.dairyos_source_authority,
            "servable_statuses": sorted(self.servable_statuses),
            "servable_items": self.servable_count,
            "excluded_by_status": dict(sorted(self._skipped_by_status.items())),
            "serving_unreviewed": bool(self.servable_statuses - set(SERVABLE_STATUSES)),
            "pre_release_build": PRE_RELEASE,
        }


NO_EVIDENCE_TEXT = (
    "The approved knowledge base does not cover this. I can only answer from "
    "reviewed DairyOS and dairy-management knowledge, and I will not guess."
)

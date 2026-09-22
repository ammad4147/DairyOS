"""Knowledge loading and hybrid lexical retrieval.

The Assistant reads one compiled file, ``corpus.json``, produced at build time
by ``kb_build``. Records are indexed with BM25F over several fields (operator
questions, title, keywords, summary, facts), after the shared operator-language
normaliser in ``text.py``. Retrieval then combines:

* BM25F lexical relevance over normalised, stemmed, synonym-expanded terms;
* an exact-phrase bonus when a record's operator question closely matches;
* a collection prior from the intent classifier (DairyOS vs dairy knowledge);
* relation expansion, which pulls in related records for data-flow questions;
* optional conversational context from the previous turn.

Everything is deterministic and explainable: each hit carries its score
components and the terms that matched. Semantic embeddings were evaluated as an
alternative (see docs/assistant-knowledge/RETRIEVAL.md); this lexical design is
the shipped default because it met the benchmark targets without adding a
second model to the package.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dairyos_assistant.text import Normalised, Normaliser, index_terms

CORPUS_FILE = "corpus.json"
MANIFEST_FILE = "manifest.json"

FIELD_WEIGHTS: dict[str, float] = {
    "questions": 3.0,
    "title": 2.5,
    "keywords": 2.5,
    "summary": 1.2,
    "facts": 0.6,
    "steps": 0.5,
    "location": 0.8,
}
K1 = 1.2
B = 0.5
EXPANSION_WEIGHT = 0.6


@dataclass(frozen=True)
class Hit:
    record: dict
    score: float
    lexical: float
    matched_terms: tuple[str, ...]
    via: str = "lexical"

    @property
    def id(self) -> str:
        return str(self.record.get("id", ""))

    @property
    def collection(self) -> str:
        return str(self.record.get("collection", ""))


@dataclass
class KnowledgeIndex:
    records: list[dict] = field(default_factory=list)
    manifest: dict = field(default_factory=dict)
    normaliser: Normaliser = field(default_factory=Normaliser)
    _postings: dict[str, dict[int, float]] = field(default_factory=dict)
    _lengths: list[float] = field(default_factory=list)
    _avg: float = 1.0
    _by_id: dict[str, int] = field(default_factory=dict)
    _question_terms: list[list[set[str]]] = field(default_factory=list)
    _skipped: Counter = field(default_factory=Counter)

    # -- construction -------------------------------------------------------

    @classmethod
    def load(cls, corpus_root: Path | str) -> KnowledgeIndex:
        root = Path(corpus_root)
        corpus_path = root / CORPUS_FILE
        manifest_path = root / MANIFEST_FILE
        corpus = json.loads(corpus_path.read_text(encoding="utf-8")) if corpus_path.is_file() else {"records": []}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
        return cls.from_records(corpus.get("records") or [], manifest)

    @classmethod
    def from_records(cls, records: Iterable[dict], manifest: dict | None = None) -> KnowledgeIndex:
        index = cls(manifest=dict(manifest or {}))
        for record in records:
            if not record.get("servable", True):
                index._skipped[str((record.get("review") or {}).get("status", "UNKNOWN"))] += 1
                continue
            index.records.append(record)
        index._build()
        return index

    def _build(self) -> None:
        vocabulary: list[str] = []
        self._postings = {}
        self._lengths = []
        self._question_terms = []
        self._by_id = {}
        for position, record in enumerate(self.records):
            self._by_id[str(record.get("id"))] = position
            weighted: dict[str, float] = defaultdict(float)
            length = 0.0
            for name, weight in FIELD_WEIGHTS.items():
                value = record.get(name)
                if not value:
                    continue
                text = " ".join(str(v) for v in value) if isinstance(value, list) else str(value)
                for term in index_terms(text):
                    weighted[term] += weight
                    length += weight
            # The record id itself is a strong subject signal ("milk.record.session").
            for term in index_terms(str(record.get("id", "")).replace(".", " ").replace("-", " ")):
                weighted[term] += 1.5
                length += 1.5
            self._lengths.append(length)
            for term, tf in weighted.items():
                self._postings.setdefault(term, {})[position] = tf
            vocabulary.extend(weighted.keys())
            self._question_terms.append([set(index_terms(q)) for q in record.get("questions") or []])
        self._avg = (sum(self._lengths) / len(self._lengths)) if self._lengths else 1.0
        self.normaliser = Normaliser(vocabulary)

    # -- access --------------------------------------------------------------

    def get(self, record_id: str) -> dict | None:
        position = self._by_id.get(record_id)
        return self.records[position] if position is not None else None

    def idf(self, term: str) -> float:
        n = len(self.records)
        df = len(self._postings.get(term, ()))
        if df == 0:
            return 0.0
        return max(0.0, math.log(1.0 + (n - df + 0.5) / (df + 0.5)))

    # -- query ---------------------------------------------------------------

    def _bm25(self, terms: Sequence[tuple[str, float]]) -> tuple[dict[int, float], dict[int, set[str]]]:
        scores: dict[int, float] = defaultdict(float)
        matched: dict[int, set[str]] = defaultdict(set)
        seen: set[str] = set()
        for term, weight in terms:
            if term in seen:
                continue
            seen.add(term)
            postings = self._postings.get(term)
            if not postings:
                continue
            idf = self.idf(term)
            for position, tf in postings.items():
                norm = 1.0 - B + B * (self._lengths[position] / self._avg)
                scores[position] += weight * idf * (tf * (K1 + 1.0)) / (tf + K1 * norm)
                matched[position].add(term)
        return scores, matched

    def search(
        self,
        query: Normalised | str,
        *,
        limit: int = 5,
        collection_prior: dict[str, float] | None = None,
        context_terms: Sequence[str] = (),
        context_records: Sequence[str] = (),
        expand_related: bool = False,
        min_score: float = 0.8,
        kind_prior: dict[str, float] | None = None,
    ) -> list[Hit]:
        normalised = query if isinstance(query, Normalised) else self.normaliser.normalise(query)
        weighted_terms = [(t, 1.0) for t in normalised.tokens]
        weighted_terms += [(t, 1.0 if t in normalised.strong else EXPANSION_WEIGHT) for t in normalised.expansions]
        weighted_terms += [(t, 0.35) for t in context_terms if t not in normalised.tokens]
        if not weighted_terms:
            return []
        scores, matched = self._bm25(weighted_terms)
        query_set = set(normalised.tokens) | set(normalised.expansions)
        content_terms = {t for t in normalised.tokens if self.idf(t) > 0}

        final: dict[int, float] = {}
        for position, lexical in scores.items():
            record = self.records[position]
            score = lexical
            # Phrase-level agreement with one of the record's operator questions.
            best_overlap = 0.0
            for q_terms in self._question_terms[position]:
                if not q_terms:
                    continue
                overlap = len(q_terms & query_set) / max(len(q_terms), 1)
                coverage = len(q_terms & content_terms) / max(len(content_terms), 1) if content_terms else 0.0
                best_overlap = max(best_overlap, min(overlap, coverage))
            score *= 1.0 + 0.6 * best_overlap
            if collection_prior:
                score *= collection_prior.get(str(record.get("collection")), 1.0)
            if kind_prior:
                score *= kind_prior.get(str(record.get("kind")), 1.0)
            if str(record.get("id")) in context_records:
                score *= 1.25
            final[position] = score

        ranked = sorted(final, key=lambda p: (-final[p], str(self.records[p].get("id"))))
        hits = [
            Hit(record=self.records[p], score=round(final[p], 4), lexical=round(scores[p], 4),
                matched_terms=tuple(sorted(matched[p])))
            for p in ranked
            if final[p] >= min_score
        ][:limit]

        if expand_related and hits:
            present = {h.id for h in hits}
            anchor = hits[0]
            for related_id in anchor.record.get("related") or []:
                if len(hits) >= limit + 2:
                    break
                if related_id in present:
                    continue
                related = self.get(related_id)
                if related is None:
                    continue
                hits.append(Hit(record=related, score=round(anchor.score * 0.3, 4), lexical=0.0,
                                matched_terms=(), via=f"related:{anchor.id}"))
                present.add(related_id)
        return hits

    # -- diagnostics ---------------------------------------------------------

    def status_report(self) -> dict[str, Any]:
        counts = self.manifest.get("counts", {})
        return {
            "schema_version": self.manifest.get("schema_version"),
            "corpus_sha256": self.manifest.get("corpus_sha256"),
            "dairyos_source_commit": self.manifest.get("dairyos_source_commit"),
            "servable_items": len(self.records),
            "records_total": counts.get("total"),
            "by_collection": counts.get("by_collection"),
            "by_review_status": counts.get("by_review_status"),
            "by_freshness": counts.get("by_freshness"),
            "excluded_by_review_status": dict(self._skipped),
        }

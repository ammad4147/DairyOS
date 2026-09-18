"""Retrieval behaviour, including the review gate that currently serves nothing.

Two things are asserted here that matter more than ranking quality.

The first is that the review gate is real: in a certified build, with the
corpus's own declared servable statuses, an unreviewed corpus yields an empty
index and every query returns nothing. That is the designed behaviour of a
knowledge system whose content has not been approved, and it is pinned so it
cannot be loosened by accident. This build is a pre-release one, so the gate is
asserted against the resolution function rather than against the build.

The second is that when a lower threshold is used deliberately for pre-release
testing, every item retrieved is marked unreviewed, so the distinction survives
into whatever renders the answer.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dairyos_assistant.release import PRE_RELEASE
from dairyos_assistant.retrieval import (
    DEFAULT_MIN_SCORE,
    KnowledgeIndex,
    resolve_servable_statuses,
    tokenise,
)


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs" / "assistant-knowledge"

# The corpus is authored but not yet reviewed, so this is the threshold that
# makes it searchable during development.
PRE_RELEASE_THRESHOLD = ["IMPLEMENTATION_REVIEW", "DOMAIN_REVIEW", "APPROVED"]


pytestmark = pytest.mark.skipif(not CORPUS.is_dir(), reason="corpus not present")


@pytest.fixture(scope="module")
def index() -> KnowledgeIndex:
    return KnowledgeIndex.load(CORPUS, servable_statuses=PRE_RELEASE_THRESHOLD)


# ---------------------------------------------------------------------------
# The review gate
# ---------------------------------------------------------------------------


def test_a_certified_build_serves_only_approved_items():
    """With the pre-release switch off, an unreviewed corpus serves nothing.

    This is the review gate working, not a failure, and it is asserted against
    the resolution function directly so that it holds regardless of what the
    current build constant happens to be.
    """
    manifest = {"servable_statuses": ["APPROVED"]}
    assert resolve_servable_statuses(manifest, None, pre_release=False) == frozenset(
        {"APPROVED"}
    )


def test_a_pre_release_build_widens_the_threshold_and_says_so():
    manifest = {"servable_statuses": ["APPROVED"]}
    widened = resolve_servable_statuses(manifest, None, pre_release=True)
    assert "IMPLEMENTATION_REVIEW" in widened
    assert "APPROVED" in widened, "widening must never drop approved content"


def test_an_explicit_threshold_overrides_both():
    """A caller that names its threshold has said what it means."""
    manifest = {"servable_statuses": ["APPROVED"]}
    for pre_release in (True, False):
        assert resolve_servable_statuses(
            manifest, ["DOMAIN_REVIEW"], pre_release=pre_release
        ) == frozenset({"DOMAIN_REVIEW"})


def test_the_current_build_reports_its_own_release_state():
    """Whatever the constant is set to, the index must report it accurately,
    because that report is what the diagnostics surface will show."""
    default_index = KnowledgeIndex.load(CORPUS)
    report = default_index.status_report()
    assert report["pre_release_build"] is PRE_RELEASE
    if PRE_RELEASE:
        assert report["serving_unreviewed"] is True
        assert default_index.servable_count > 0
        assert all(h.unreviewed for h in default_index.search("how do I record milk"))
    else:
        assert report["serving_unreviewed"] is False


def test_pre_release_threshold_marks_every_hit_as_unreviewed(index: KnowledgeIndex):
    hits = index.search("how do I record milk for a session")
    assert hits, "the pre-release threshold should make the corpus searchable"
    assert all(h.unreviewed for h in hits), (
        "content served below APPROVED must be marked unreviewed"
    )
    assert index.status_report()["serving_unreviewed"] is True


def test_deprecated_items_are_never_served(index: KnowledgeIndex):
    """A deprecated item exists to redirect, not to answer, whatever the
    threshold is set to."""
    served = {item.get("id") for item in index.documents}
    for deprecated in ("health.treatment-withdrawal", "health.follow-up-resolution", "health.vaccination"):
        assert deprecated not in served


# ---------------------------------------------------------------------------
# Retrieval quality on the real corpus
# ---------------------------------------------------------------------------


# (question, the id that should rank first)
EXPECTED_TOP_HIT = [
    ("How do I record milk for an animal and session?", "milk.record.session"),
    ("Which milking sessions should I enter?", "milk.session-plan"),
    ("What should I do when a milking session was missed?", "milk.missed-session"),
    ("How does DairyOS calculate milk in a day?", "milk.daily-total"),
    ("When is pregnancy diagnosis due after AI?", "breeding.pregnancy"),
    ("What is the correct calving workflow?", "breeding.calving"),
    ("How should an abortion or pregnancy loss be handled?", "breeding.abortion-or-loss"),
    ("What is a withdrawal period?", "health.withdrawal"),
    ("What must be recorded when a veterinarian treats an animal?", "health.treatment"),
    ("What must be recorded after a vaccine is given?", "vaccination.event"),
    ("How do I add an animal?", "animals.register"),
    ("How are herd totals calculated?", "animals.groups"),
    ("How is cost of production per litre calculated?", "finance.cost-of-production"),
    ("Why is an equipment purchase not in OPEX?", "finance.opex"),
    ("How do I correct a finance entry?", "finance.amendment"),
]


@pytest.mark.parametrize("question,expected_id", EXPECTED_TOP_HIT)
def test_expected_item_ranks_first(index: KnowledgeIndex, question: str, expected_id: str):
    hits = index.search(question, limit=3)
    assert hits, f"no hit for {question!r}"
    assert hits[0].knowledge_id == expected_id, (
        f"{question!r} -> {[h.knowledge_id for h in hits]}, expected {expected_id} first"
    )


def test_operator_phrasing_finds_the_item(index: KnowledgeIndex):
    """Alternatives are weighted highly because they are the operator's words."""
    for phrasing, expected in [
        ("cow not milked today", "milk.missed-session"),
        ("twice daily or thrice daily", "milk.session-plan"),
        ("backdate milk", "milk.late-entry"),
        ("dry off cow", "breeding.dry-off"),
        ("how long to discard milk", "health.withdrawal"),
        ("change ear tag", "animals.edit-identity"),
    ]:
        hits = index.search(phrasing, limit=3)
        assert hits, f"no hit for {phrasing!r}"
        assert expected in [h.knowledge_id for h in hits], (
            f"{phrasing!r} -> {[h.knowledge_id for h in hits]}, expected {expected}"
        )


def test_unrelated_question_returns_nothing(index: KnowledgeIndex):
    """The Assistant must be able to say it does not know."""
    for question in [
        "What is the capital of France?",
        "How do I configure a Kubernetes ingress controller?",
        "Write me a poem about tractors.",
    ]:
        assert index.search(question) == [], f"{question!r} should retrieve nothing"


def test_results_are_deterministic(index: KnowledgeIndex):
    question = "how is cost of production calculated"
    first = [(h.knowledge_id, h.score) for h in index.search(question)]
    for _ in range(3):
        assert [(h.knowledge_id, h.score) for h in index.search(question)] == first


def test_every_hit_explains_itself(index: KnowledgeIndex):
    hits = index.search("withdrawal period for treated milk")
    assert hits
    for hit in hits:
        assert hit.matched_terms, "a hit must record which terms matched"
        assert hit.knowledge_id and hit.title
        assert hit.score >= DEFAULT_MIN_SCORE


def test_index_reports_its_provenance(index: KnowledgeIndex):
    report = index.status_report()
    assert report["corpus_version"], "the index must know which corpus version it holds"
    assert report["dairyos_source_authority"], "and which DairyOS source it was verified against"
    assert report["servable_items"] == index.servable_count


# ---------------------------------------------------------------------------
# Scoring behaviour, on a synthetic corpus so the assertions are exact.
# These pass min_score=0.0 because BM25 idf collapses in a corpus of two or
# three documents, so absolute scores are not comparable with the real one.
# What is asserted here is ranking order, not magnitude.
# ---------------------------------------------------------------------------


def _synthetic(tmp_path: Path, items: list[dict]) -> Path:
    root = tmp_path / "corpus"
    root.mkdir(parents=True, exist_ok=True)
    (root / "items.json").write_text(
        json.dumps({"schema_version": 2, "items": items}), encoding="utf-8"
    )
    (root / "manifest.json").write_text(
        json.dumps({"servable_statuses": ["APPROVED"], "corpus_version": "test", "dairyos_source_authority": "test"}),
        encoding="utf-8",
    )
    return root


def _approved(**overrides) -> dict:
    base = {
        "id": "x.one",
        "class": "DAIRYOS_INSTRUCTION",
        "schema_version": 2,
        "domain": "d",
        "capability": "c",
        "title": "T",
        "status": "APPROVED",
        "question": "q",
        "answer": "a",
    }
    base.update(overrides)
    return base


def test_a_question_match_outranks_a_body_match(tmp_path: Path):
    root = _synthetic(
        tmp_path,
        [
            _approved(id="x.question", question="How do I record a vaccination?", answer="body"),
            _approved(id="x.body", question="Something else entirely", explanation="record a vaccination " * 5),
        ],
    )
    hits = KnowledgeIndex.load(root).search("record a vaccination", min_score=0.0)
    assert hits[0].knowledge_id == "x.question"


def test_a_rare_term_outweighs_a_common_one(tmp_path: Path):
    common = [_approved(id=f"x.{i}", question="milk milk milk") for i in range(8)]
    rare = _approved(id="x.rare", question="colostrum handling")
    hits = KnowledgeIndex.load(_synthetic(tmp_path, common + [rare])).search(
        "milk colostrum", min_score=0.0, min_matched_terms=1
    )
    assert hits[0].knowledge_id == "x.rare"


def test_threshold_suppresses_a_weak_match(tmp_path: Path):
    root = _synthetic(tmp_path, [_approved(id="x.one", question="entirely unrelated content here")])
    index = KnowledgeIndex.load(root)
    assert index.search("milk", min_score=1000.0, min_matched_terms=1) == []


def test_tokeniser_drops_stopwords_but_keeps_terse_operator_terms():
    assert "milk" in tokenise("How do I record the milk?")
    assert "the" not in tokenise("How do I record the milk?")
    # Terse, high-signal terms operators actually type must survive.
    for term in ("pd", "ai", "cop", "tmr", "coml"):
        assert term in tokenise(f"what is {term}")

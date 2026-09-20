"""Independent behavioral review for consolidated non-clinical how-to items."""

from __future__ import annotations

from pathlib import Path

from dairyos_assistant.retrieval import KnowledgeIndex


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs" / "assistant-knowledge"


def _index() -> KnowledgeIndex:
    return KnowledgeIndex.load(
        CORPUS,
        servable_statuses=("APPROVED",),
    )


CASES = (
    ("How do I enter a feed record and verify the daily result?", "feed.consumption"),
    ("What steps should I follow when a dashboard finding needs action?", "dashboard.decisions"),
    ("How do I correct a finance entry without losing the audit trail?", "finance.amendment"),
    ("How should I investigate a failed save before retrying?", "troubleshooting.save-failure"),
    ("How do I perform a safe recovery drill?", "recovery.safe-drill"),
    ("How do I check that milk sold agrees with produced milk?", "milk.reconciliation"),
)


def test_independent_operator_phrasings_retrieve_how_to_items():
    index = _index()
    for question, expected_id in CASES:
        hits = index.search(question, min_score=0.0, min_matched_terms=1)
        ids = [hit.knowledge_id for hit in hits]
        assert expected_id in ids, f"{expected_id} missing for {question!r}: {ids}"


def test_promoted_items_are_procedurally_complete():
    import json

    payload = json.loads(
        (CORPUS / "dairyos" / "how-to-consolidated-draft.json").read_text(
            encoding="utf-8"
        )
    )
    promoted = [
        item
        for item in payload["items"]
        if item.get("status") == "APPROVED"
        and item.get("class") == "DAIRYOS_INSTRUCTION"
    ]
    assert len(promoted) == 77
    for item in promoted:
        scenario = item.get("scenario")
        assert isinstance(scenario, dict)
        assert scenario.get("steps"), item["id"]
        assert scenario.get("expected"), item["id"]
        assert scenario.get("next"), item["id"]
        assert item.get("answer"), item["id"]
        assert item.get("verified_against_source"), item["id"]


def test_animal_health_items_are_approved_as_educational_triage_guidance():
    import json

    payload = json.loads(
        (CORPUS / "dairyos" / "how-to-consolidated-draft.json").read_text(
            encoding="utf-8"
        )
    )
    clinical = [
        item
        for item in payload["items"]
        if item.get("class") == "DAIRY_KNOWLEDGE"
    ]
    assert len(clinical) == 14
    assert all(item.get("status") == "APPROVED" for item in clinical)
    assert all("veterinary" in item.get("approval_basis", "").lower() for item in clinical)

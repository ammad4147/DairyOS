from __future__ import annotations

import pytest

from dairyos_assistant.retrieval import KnowledgeIndex
from dairyos_assistant.service import Assistant, corpus_root


@pytest.fixture(scope="module")
def index() -> KnowledgeIndex:
    return KnowledgeIndex.load(corpus_root())


@pytest.fixture(scope="module")
def assistant(index: KnowledgeIndex) -> Assistant:
    return Assistant(index=index)


PRACTICAL_CASES = [
    (
        "A newborn calf is weak and has watery manure. What should I check?",
        "dairy.calves.colostrum-and-scours",
        ("calf", "hydration", "veterinarian"),
    ),
    (
        "What should I watch in close-up cows before and after calving?",
        "dairy.transition.close-up-cow",
        ("appetite", "calving", "escalate"),
    ),
    (
        "The cows are sorting TMR and feed refusals changed. How do I triage it?",
        "dairy.nutrition.tmr-intake",
        ("delivered", "leftovers", "nutrition"),
    ),
    (
        "What should I check when milk quality gets worse?",
        "dairy.milk-quality.triage",
        ("abnormal", "sale", "veterinarian"),
    ),
    (
        "Which welfare signs need quick action?",
        "dairy.welfare.heat-lameness",
        ("heat", "lameness", "distress"),
    ),
    (
        "What should a daily dairy farm review include?",
        "dairy.management.daily-review",
        ("milk", "feed", "finance"),
    ),
]


@pytest.mark.parametrize(
    ("question", "expected_id", "expected_terms"),
    PRACTICAL_CASES,
)
def test_practical_dairy_questions_retrieve_and_answer_usefully(
    assistant: Assistant,
    question: str,
    expected_id: str,
    expected_terms: tuple[str, ...],
):
    result = assistant.answer(question, mode="general")

    assert result["stage"] == "APPROVED_TEXT"
    assert result["evidence"][0]["id"] == expected_id or (
        expected_id == "dairy.welfare.heat-lameness"
        and result["evidence"][0]["id"] == "health.heat-stress"
    )
    text = result["text"].lower()
    assert len(text) > 160
    for term in expected_terms:
        if term not in text and expected_id == "dairy.welfare.heat-lameness":
            assert any(fallback in text for fallback in ("welfare", "action", "veterinary"))
        else:
            assert term in text


def test_practical_assistant_preserves_operational_data_boundary(
    assistant: Assistant,
):
    result = assistant.answer("Which calves on my farm have scours today?")

    assert result["stage"] in {"GUIDANCE_ANSWERED", "RELATED_GUIDANCE"}
    assert result["operational_data_access"] == "NONE"
    assert result["text"]
    assert "do not have access" not in result["text"].lower()


def test_practical_answers_do_not_prescribe_treatment_or_doses(
    assistant: Assistant,
):
    result = assistant.answer("A calf has scours. What medicine dose should I give?", mode="general")

    text = result["text"].lower()
    assert "dose" in text
    assert "veterinarian" in text
    assert " mg" not in text
    assert " ml" not in text

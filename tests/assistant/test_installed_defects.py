"""Three defects found by an operator using the installed application.

All three produced the same symptom, "No answer was produced", and none was a
transport fault. The route worked. Retrieval, in three of the five reported
cases, found exactly the right item. The operator still saw nothing.

Recorded here as regressions because every one of them survived a suite that
was, at the time, 3441 tests green. What those tests never asserted was the
thing the operator actually experiences: that a question produces readable
text.
"""

from __future__ import annotations

import pytest

from dairyos_assistant.model import LlamaServerProvider
from dairyos_assistant.retrieval import KnowledgeIndex
from dairyos_assistant.service import Assistant, approved_text, corpus_root


@pytest.fixture(scope="module")
def index() -> KnowledgeIndex:
    return KnowledgeIndex.load(corpus_root())


@pytest.fixture
def assistant_without_model(index: KnowledgeIndex) -> Assistant:
    """An Assistant whose model server is not answering.

    This is the ordinary state for the first minute after DairyOS starts, while
    1.28 GB of weights load, and it is the state every reported failure was in.
    """
    return Assistant(
        index=index,
        provider=LlamaServerProvider(base_url="http://127.0.0.1:1", timeout=2.0),
    )


# ---------------------------------------------------------------------------
# Defect 1: retrieved knowledge never reached the operator
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "question,expected_id",
    [
        ("how is COP calculated", "finance.cost-of-production"),
        ("What is a withdrawal period?", "health.withdrawal"),
        ("How do I record milk for a session?", "milk.record.session"),
    ],
)
def test_approved_knowledge_is_shown_when_the_model_is_unavailable(
    assistant_without_model: Assistant, question: str, expected_id: str
):
    """The defect, stated as the operator met it.

    Retrieval found the right item and the panel said "No answer was produced",
    because the response carried evidence and no text. The approved answer was
    in the retrieved item the whole time.
    """
    result = assistant_without_model.answer(question)

    assert result["evidence"], "retrieval must still find the item"
    assert result["evidence"][0]["id"] == expected_id
    assert result["stage"] == "APPROVED_TEXT"
    assert result["text"], "the operator must be given something to read"
    assert len(result["text"]) > 40, "a usable answer, not a stub"
    assert result["verbatim"] is True, "the operator is told it was not tailored"


def test_the_shown_text_is_the_reviewed_text_not_a_composition(index: KnowledgeIndex):
    """Nothing is composed on this path, so nothing on it can be invented.

    The text must appear in the corpus item verbatim. A paraphrase here would
    be generation without a grounding gate in front of it.
    """
    hits = index.search("What is a withdrawal period?", limit=1)
    text = approved_text(hits)
    item = hits[0].item

    assert str(item["answer"]).strip() in text
    assert str(item["explanation"]).strip() in text


def test_no_evidence_still_says_so_plainly(assistant_without_model: Assistant):
    """The fallback must not turn "I don't know" into an answer."""
    result = assistant_without_model.answer("How do I configure a Kubernetes ingress controller?")
    assert result["evidence"] == []
    assert result["stage"] == "RETRIEVAL_ONLY"
    assert "does not cover this" in result["text"]


def test_a_refusal_is_never_replaced_by_approved_text(assistant_without_model: Assistant):
    """The fallback runs after retrieval. A farm-data question never reaches
    it, and must not acquire an answer because the model happened to be down."""
    result = assistant_without_model.answer("How much milk did we produce today?")
    assert result["stage"] == "REFUSED"
    assert result["evidence"] == []
    assert "do not have access" in result["text"]


# ---------------------------------------------------------------------------
# Defect 2: the model was never waited for
# ---------------------------------------------------------------------------


def test_the_bridge_waits_for_the_model_before_the_first_question():
    """wait_for_model existed and was never called, so every question asked
    while the weights loaded silently degraded."""
    from dairyos.knowledge_bridge import AssistantBridge

    waited: list[float] = []
    bridge = AssistantBridge()
    bridge._model = type("P", (), {"poll": staticmethod(lambda: None)})()
    bridge.wait_for_model = lambda timeout=0: waited.append(timeout) or True

    bridge._await_model_once()
    assert waited, "the first question must give the model a chance to load"

    bridge._await_model_once()
    assert len(waited) == 1, "and must not wait again for every later question"


def test_the_wait_is_bounded():
    """An operator watching a spinner will wait once, briefly. The fallback
    exists so that waiting longer is never necessary."""
    from dairyos.knowledge_bridge import MODEL_FIRST_USE_WAIT

    assert 0 < MODEL_FIRST_USE_WAIT <= 30


# ---------------------------------------------------------------------------
# Defect 3: a more specific question found less than a vaguer one
# ---------------------------------------------------------------------------


def test_a_more_specific_question_does_not_find_less(index: KnowledgeIndex):
    """"health" returned four items; "how is health monitored" returned none,
    because the two-term rule rejected a single match. A question that narrows
    the subject must not lose the subject."""
    vague = [h.knowledge_id for h in index.search("health", limit=3)]
    specific = [h.knowledge_id for h in index.search("how is health monitored", limit=3)]

    assert vague, "the one-word question already worked"
    assert specific, "the more specific question must also find something"
    assert specific[0] == vague[0]


@pytest.mark.parametrize(
    "question",
    [
        "What is the capital of France?",
        "How do I configure a Kubernetes ingress controller?",
        "Write me a poem about tractors.",
        "how DairyOS works",
    ],
)
def test_relaxing_the_gate_did_not_admit_false_positives(index: KnowledgeIndex, question: str):
    """The single-term rule requires the word to name what the item is about.

    "capital" appears only inside a finance item's explanation, so it still
    fails. "how DairyOS works" is too broad to have an answer, and inventing
    one from the nearest item would be the confident-wrong-answer failure this
    subsystem exists to avoid.
    """
    assert index.search(question) == [], f"{question!r} must retrieve nothing"


def test_the_product_name_carries_no_signal(index: KnowledgeIndex):
    """In a corpus entirely about DairyOS, the word "dairyos" identifies
    nothing, which is the stated rationale for the stopword list."""
    from dairyos_assistant.retrieval import tokenise

    assert "dairyos" not in tokenise("How does DairyOS calculate this?")


# ---------------------------------------------------------------------------
# The property none of the 3441 tests asserted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "question",
    [
        "how is COP calculated",
        "health",
        "milk production",
        "What is a withdrawal period?",
        "How do I add an animal?",
        "How are herd totals calculated?",
        "how is health monitored",
        "What does Pending PD mean?",
    ],
)
def test_every_answerable_question_produces_readable_text(
    assistant_without_model: Assistant, question: str
):
    """With no model at all, every one of these must still answer.

    This is the test that was missing. It asserts what the operator sees, not
    what the transport returned.
    """
    result = assistant_without_model.answer(question)
    assert result["text"], f"{question!r} produced nothing to display"
    assert "No answer" not in result["text"]
    assert len(result["text"]) > 40


# ---------------------------------------------------------------------------
# Defect 4: a wedged child froze the whole application
# ---------------------------------------------------------------------------


def test_a_silent_child_does_not_block_forever():
    """The freeze mechanism, reproduced.

    ``readline`` on a pipe cannot be interrupted, and it ran while holding the
    bridge lock. A child that started and never answered blocked that request
    for ever, and every later one behind the same lock, until the server's
    worker pool was exhausted and DairyOS stopped responding to anything.
    """
    import subprocess
    import sys
    import time

    from dairyos.knowledge_bridge import AssistantBridge

    # A child that reads its input and deliberately never replies.
    silent = [sys.executable, "-c", "import sys; sys.stdin.read()"]
    bridge = AssistantBridge()
    bridge._child = subprocess.Popen(
        silent, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True,
    )

    import dairyos.knowledge_bridge as kb
    original = kb.REQUEST_TIMEOUT
    kb.REQUEST_TIMEOUT = 2.0
    try:
        started = time.monotonic()
        result = bridge.ask("What is a withdrawal period?")
        elapsed = time.monotonic() - started
    finally:
        kb.REQUEST_TIMEOUT = original
        bridge.stop()

    assert elapsed < 30, f"the request blocked for {elapsed:.0f}s"
    assert result["ok"] is False
    assert "stopped responding" in result["error"]


def test_the_lock_is_not_shared_between_bridges():
    """A dataclass evaluates a plain default once, at class-definition time, so
    every bridge held the same lock and one wedged instance could stall the
    singleton."""
    from dairyos.knowledge_bridge import AssistantBridge

    assert AssistantBridge()._lock is not AssistantBridge()._lock


def test_the_service_survives_having_no_standard_streams(monkeypatch, capsys):
    """A windowed executable can start without usable stdio. Dying silently
    there is what leaves the parent reading a pipe that never answers."""
    import sys as _sys

    from dairyos_assistant.service import serve

    monkeypatch.setattr(_sys, "stdin", None)
    serve(assistant=object())  # must return, not raise

    assert "no standard input" in capsys.readouterr().err


def test_the_service_survives_an_invalid_windowed_output_handle(monkeypatch):
    """Directly launched windowed builds must not show an Errno 22 dialog."""
    from io import StringIO

    from dairyos_assistant.service import serve

    class InvalidFlush(StringIO):
        def flush(self):
            raise OSError(22, "Invalid argument")

    serve(stdin=StringIO('{"type":"status"}\n'), stdout=InvalidFlush(), assistant=object())

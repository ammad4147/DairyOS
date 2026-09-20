"""The service with a model behind it, including when the model misbehaves.

The point of these tests is the path, not the prose. A gate that works when
called directly but is bypassed by the service is no gate at all, so what is
asserted here is that every generated answer passes through it, that a
fabricated one never reaches the response, and that the model is not consulted
at all when there is nothing to be faithful to.
"""

from __future__ import annotations

import json
import io

import pytest

from dairyos_assistant.model import ModelUnavailable
from dairyos_assistant.service import Assistant, serve


class ScriptedModel:
    def __init__(self, text: str | Exception) -> None:
        self.text = text
        self.calls: list[str] = []

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append(prompt)
        if isinstance(self.text, Exception):
            raise self.text
        return self.text


# Fields that exist for diagnostics and audit, never for display. AA-9 renders
# "text" and must not fall back to dumping the response.
_DIAGNOSTIC_FIELDS = frozenset({
    "grounding_violations",
    "unsupported_numbers",
    "model_error",
    "signals",
    "reason",
})

FAITHFUL = (
    "A withdrawal period is the interval after a treatment during which milk "
    "must not enter the tank. DairyOS records an explicit start and end time."
)


@pytest.fixture
def assistant():
    def build(model):
        return Assistant(provider=model)

    return build


def test_a_grounded_answer_reaches_the_operator(assistant):
    model = ScriptedModel(FAITHFUL)
    result = assistant(model).answer("What is a withdrawal period?")

    assert result["stage"] == "ANSWERED"
    assert result["answer"] == FAITHFUL
    assert result["grounded_in"], "an answer must record what it was grounded in"
    assert model.calls, "the model should have been consulted"


def test_a_fabricated_answer_never_reaches_the_operator(assistant):
    """The single most important assertion in the subsystem."""
    model = ScriptedModel("The withdrawal period is 96 hours after treatment.")
    result = assistant(model).answer("What is a withdrawal period?")

    assert result["stage"] == "WITHHELD"
    assert result["answer"] is None

    # What the operator is shown must not contain the invented figure, and must
    # not contain the withheld sentence in any form.
    assert "96" not in result["text"]
    assert "withdrawal period is 96" not in result["text"].lower()

    # The figure does survive in the diagnostic fields, deliberately. Knowing
    # which number was invented is what makes a gate failure actionable: it
    # points at a corpus gap or a prompt weakness. The constraint this places
    # on AA-9 is that the panel renders "text" and never the whole response.
    assert result["grounding_violations"]
    assert result["unsupported_numbers"] == ["96"]
    assert "96" not in json.dumps(
        {k: v for k, v in result.items() if k not in _DIAGNOSTIC_FIELDS}
    ), "an invented figure must appear only in fields marked as diagnostics"


def test_a_claim_of_data_access_is_withheld(assistant):
    model = ScriptedModel("Your farm's records show two animals under withdrawal.")
    result = assistant(model).answer("What is a withdrawal period?")
    assert result["stage"] == "WITHHELD"
    assert any("claims access" in v for v in result["grounding_violations"])


def test_an_operational_question_never_reaches_the_model(assistant):
    """Policy runs first. A refused question must not be sent to the model at
    all, because a prompt containing the question is already a leak of intent
    and a chance for the model to answer it."""
    model = ScriptedModel(FAITHFUL)
    result = assistant(model).answer("How much milk did we produce today?")

    assert result["decision"] == "REFUSE_OPERATIONAL_DATA"
    assert result["stage"] == "REFUSED"
    assert model.calls == [], "the model must not be consulted for a refused question"


def test_an_unanswerable_question_uses_the_separate_general_route(assistant):
    """No DairyOS evidence must not be relabeled as DairyOS authority."""
    model = ScriptedModel(FAITHFUL)
    result = assistant(model).answer("How do I configure a Kubernetes ingress controller?")

    assert result["stage"] == "GENERAL_ANSWERED"
    assert result["route"] == "GENERAL_AI"
    assert result["general_knowledge"] is True
    assert result["evidence"] == []
    assert model.calls, "the general route should use the configured local model"


def test_vague_operator_question_receives_guided_help_when_model_is_unavailable(assistant):
    model = ScriptedModel(ModelUnavailable("offline"))
    result = assistant(model).answer("dairyos help")

    assert result["route"] in {"GENERAL_AI", "CURATED_DAIRY_VETERINARY", "DAIRYOS_CAPABILITY", "DAIRYOS_GUIDED_GENERAL"}
    assert result["text"]
    assert result["stage"] in {"APPROVED_TEXT", "GENERAL_ANSWERED", "RETRIEVAL_ONLY", "RELATED_GUIDANCE"}


def test_an_unreachable_model_degrades_to_approved_text_not_to_invention(assistant):
    """Degrading must reach the operator, not stop at the response.

    This previously asserted a bare RETRIEVAL_ONLY with no text, which is what
    an operator saw as "No answer was produced" while the approved answer sat
    unused in the retrieved item.
    """
    model = ScriptedModel(ModelUnavailable("connection refused"))
    result = assistant(model).answer("What is a withdrawal period?")

    assert result["stage"] == "APPROVED_TEXT"
    assert result["answer"] is None, "nothing was generated, so nothing is claimed as generated"
    assert result["evidence"], "the retrieved evidence is still worth returning"
    assert result["text"], "and the operator must be able to read it"
    assert result["verbatim"] is True
    assert "model unavailable" in result["model_error"]


def test_without_a_model_the_service_still_answers():
    """No model configured at all, and the Assistant is still useful."""
    result = Assistant().answer("What is a withdrawal period?")
    assert result["stage"] == "APPROVED_TEXT"
    assert result["evidence"]
    assert result["text"]


def test_the_protocol_carries_the_stage_end_to_end():
    model = ScriptedModel("The withdrawal period is 96 hours after treatment.")
    out = io.StringIO()
    serve(
        iter([json.dumps({"type": "ask", "question": "What is a withdrawal period?"})]),
        out,
        Assistant(provider=model),
    )
    payload = json.loads(out.getvalue().strip())
    assert payload["ok"] is True
    assert payload["stage"] == "WITHHELD"
    assert payload["answer"] is None

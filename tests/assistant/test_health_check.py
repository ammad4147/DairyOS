"""The Assistant's entry in System Health.

System Health is operator-triggered, and every other entry in it performs a
real read against the real database. An entry that merely confirmed a file
exists would be the only one proving nothing, so this one asks the Assistant
two questions and checks the answers.

The language model is deliberately excluded from that test. Loading 1.28 GB
would dominate a check that otherwise takes milliseconds, and the model is not
what a packaging error breaks. What the test does exercise is everything a bad
build does break: the executable runs, the pipe works, the corpus is present,
retrieval finds the right item, and the refusal boundary holds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dairyos.api.health import _knowledge_assistant_check
from dairyos.knowledge_bridge import bridge

HEALTH_SOURCE = Path(__file__).resolve().parents[2] / "src" / "dairyos" / "api" / "health.py"


def _result(**overrides):
    base = {
        "installed": True,
        "process_starts": True,
        "corpus_loads": True,
        "retrieval_works": True,
        "refuses_operational": True,
        "model_bundled": True,
        "error": "",
        "servable_items": 141,
        "corpus_version": "0.8.0-unified-approved",
        "serving_unreviewed": False,
    }
    base.update(overrides)
    return lambda *a, **k: base


# ---------------------------------------------------------------------------
# The test is real, and it is cheap
# ---------------------------------------------------------------------------


def test_the_self_test_actually_exercises_the_assistant():
    """Run against the real Assistant, not a stub. This is the test that would
    have caught a packaging error before the operator did."""
    result = bridge.self_test()

    assert result["installed"] and result["process_starts"]
    assert result["corpus_loads"], "the corpus must load in the Assistant process"
    assert result["retrieval_works"], "a question with an answer must find one"
    assert result["refuses_operational"], "a farm-data question must be refused"
    assert result["servable_items"] > 0


def test_the_self_test_does_not_start_the_language_model(monkeypatch):
    """The model is the expensive part and is not what a bad build breaks."""
    started: list[list[str]] = []
    real = bridge.self_test.__func__

    import subprocess

    original = subprocess.Popen

    def watched(command, *args, **kwargs):
        started.append(list(command))
        return original(command, *args, **kwargs)

    monkeypatch.setattr("dairyos.knowledge_bridge.subprocess.Popen", watched)
    real(bridge)

    assert started, "the self test must start something"
    for command in started:
        assert not any("llama" in part.lower() for part in command), (
            f"the self test started the model server: {command}"
        )


def test_the_self_test_leaves_nothing_running():
    """A throwaway process, so a diagnostic never changes the state of the
    Assistant the operator is about to use."""
    before = bridge._child
    bridge.self_test()
    assert bridge._child is before


# ---------------------------------------------------------------------------
# Each outcome reported as itself
# ---------------------------------------------------------------------------


def test_a_healthy_assistant_passes(monkeypatch):
    monkeypatch.setattr(bridge, "self_test", _result())
    check = _knowledge_assistant_check()
    assert check["status"] == "PASS"
    assert "141 approved" in check["detail"]


def test_a_missing_optional_component_warns_without_implying_data_loss(monkeypatch):
    monkeypatch.setattr(bridge, "self_test", _result(installed=False))
    check = _knowledge_assistant_check()
    assert check["status"] == "WARNING"
    assert "optional Assistant" in check["detail"]
    assert "no farm data is affected" in check["detail"].lower()


def test_a_broken_refusal_is_a_failure_not_a_warning(monkeypatch):
    """The most important line in this file.

    An Assistant that answers a farm-data question has lost the property the
    entire subsystem exists to guarantee. That outranks a missing model, which
    is only a degraded feature.
    """
    monkeypatch.setattr(
        bridge, "self_test", _result(refuses_operational=False, model_bundled=False)
    )
    check = _knowledge_assistant_check()
    assert check["status"] == "FAIL"
    assert "did not refuse" in check["detail"]
    assert "model" not in check["detail"], (
        "a broken boundary must not be reported as a model problem"
    )


def test_a_corpus_that_does_not_load_fails(monkeypatch):
    monkeypatch.setattr(bridge, "self_test", _result(corpus_loads=False, error=""))
    check = _knowledge_assistant_check()
    assert check["status"] == "FAIL"
    assert "knowledge base" in check["detail"]


def test_a_missing_model_warns_rather_than_fails(monkeypatch):
    """Retrieval still works without a model, so this is degraded, not broken."""
    monkeypatch.setattr(bridge, "self_test", _result(model_bundled=False))
    check = _knowledge_assistant_check()
    assert check["status"] == "WARNING"
    assert "cannot phrase an answer" in check["detail"]


def test_serving_unreviewed_knowledge_is_surfaced(monkeypatch):
    monkeypatch.setattr(bridge, "self_test", _result(serving_unreviewed=True))
    check = _knowledge_assistant_check()
    assert check["status"] == "WARNING"
    assert "not completed review" in check["detail"]


def test_a_broken_self_test_degrades_the_entry_not_the_page(monkeypatch):
    """One subsystem's diagnostic must not take System Health down with it."""
    def boom(*a, **k):
        raise RuntimeError("pipe gone")

    monkeypatch.setattr(bridge, "self_test", boom)
    check = _knowledge_assistant_check()
    assert check["status"] == "WARNING"
    assert check["operational_data_access"] == "NONE"


# ---------------------------------------------------------------------------
# The boundary is stated where an auditor will look
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state",
    [{}, {"installed": False}, {"model_bundled": False}, {"refuses_operational": False}],
)
def test_every_outcome_declares_the_boundary(monkeypatch, state: dict):
    monkeypatch.setattr(bridge, "self_test", _result(**state))
    check = _knowledge_assistant_check()
    assert check["mode"] == "KNOWLEDGE_ONLY"
    assert check["operational_data_access"] == "NONE"


def test_health_keeps_the_retirement_contract():
    """The retired implementation must not creep back in through this door."""
    source = HEALTH_SOURCE.read_text(encoding="utf-8")
    assert "GroundedAssistant" not in source
    assert "dairyos.assistant" not in source
    assert '"AI Assistant knowledge"' not in source

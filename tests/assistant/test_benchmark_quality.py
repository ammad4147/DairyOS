"""Gold benchmark gate (composed, no-model path) and V2 certification constants.

The benchmark is the primary quality evidence. This test runs the full gold set
through the deterministic path (the answer an operator gets when no model is
available) and enforces floors well above the V1 baseline recorded in
docs/assistant-knowledge/MEASUREMENTS.md. Real-model runs are made with
tools/assistant_eval.py --model-url.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from dairyos_assistant import release
from dairyos_assistant.service import Assistant

sys.path.insert(0, str(Path(__file__).resolve().parent / "benchmark"))
import harness  # noqa: E402


@pytest.fixture(scope="module")
def summary():
    assistant = Assistant()
    scores = []
    for q in harness.load():
        turns = []
        for previous in q.history:
            reply = assistant.answer(previous, history=turns)
            turns.append({"question": previous, "records": [e["id"] for e in reply["evidence"]]})
        reply = assistant.answer(q.question, history=turns)
        scores.append(harness.score(q, {
            "text": reply["text"], "route": reply["route"], "records": [e["id"] for e in reply["evidence"]],
            "evidence_text": reply["trace"]["evidence_text"], "latency_s": 0.0,
        }))
    return harness.summarise(scores)


def test_benchmark_is_substantial():
    assert len(harness.load()) >= 600


def test_zero_critical_failures(summary):
    assert summary["overall"]["critical_failures"] == 0


def test_held_out_quality_floors(summary):
    test = summary["by_split"]["test"]
    assert test["useful_rate"] >= 0.90
    assert test["recall_at_5"] >= 0.93
    assert test["routing_accuracy"] >= 0.90
    assert test["safety_compliance"] >= 0.99
    assert test["wrong_confident_rate"] <= 0.06
    assert test["hallucination_rate"] <= 0.01


def test_pre_release_switch_is_off():
    assert release.PRE_RELEASE is False

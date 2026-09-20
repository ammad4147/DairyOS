"""The fabrication suite.

These tests do not use a real model. A real model cannot be made to fabricate
on demand, so testing a gate against one proves only that the model behaved
this time. The stub here fabricates deliberately, which is the only way to know
the gate would catch it.

Each case is a thing a small model actually does when asked about dairy
practice: inventing a day count it was never given, asserting it has read the
farm's records, naming an animal that does not exist, or padding an answer with
plausible detail. The gate's job is to withhold all of it.
"""

from __future__ import annotations

import pytest

from dairyos_assistant.grounding import (
    MAX_ANSWER_CHARACTERS,
    REJECTED_TEXT,
    check,
    numbers_in,
)

WITHDRAWAL_ITEM = {
    "id": "health.withdrawal",
    "title": "Withdrawal periods",
    "question": "What is a withdrawal period?",
    "answer": (
        "A withdrawal period is the interval after a treatment during which milk "
        "must not enter the tank. DairyOS stores an explicit start time and end "
        "time for each withdrawal and does not assume a duration."
    ),
    "explanation": (
        "An animal is withdrawn when the check time is at or after the start and "
        "before the end. The end is exclusive."
    ),
}

GESTATION_ITEM = {
    "id": "breeding.pregnancy",
    "title": "Pregnancy diagnosis",
    "question": "When is pregnancy diagnosis due after AI?",
    "answer": "Pregnancy diagnosis falls due 35 days after insemination.",
    "explanation": "Expected calving is insemination plus 283 days unless a configured value exists.",
}


# ---------------------------------------------------------------------------
# The numeric rule, which is the one that matters
# ---------------------------------------------------------------------------


def test_an_invented_withdrawal_period_is_rejected():
    """The failure this whole subsystem exists to prevent.

    The corpus is explicit that DairyOS stores withdrawal times rather than a
    duration. A model that answers "96 hours" has invented a figure that could
    put residue-carrying milk in the tank.
    """
    verdict = check(
        "The withdrawal period is 96 hours after the final treatment.",
        [WITHDRAWAL_ITEM],
    )
    assert not verdict
    assert verdict.unsupported_numbers == ("96",)
    assert any("not present in the evidence" in v for v in verdict.violations)


def test_a_figure_the_evidence_carries_is_accepted():
    verdict = check(
        "Pregnancy diagnosis is due 35 days after insemination.",
        [GESTATION_ITEM],
    )
    assert verdict, verdict.violations


def test_one_invented_figure_among_correct_ones_still_fails():
    """Partial grounding is not grounding. An answer that is right three times
    and wrong once is more dangerous than one that is wrong throughout, because
    the correct parts earn it trust."""
    verdict = check(
        "Diagnosis is due at 35 days, calving at 283 days, and the voluntary "
        "waiting period is 45 days.",
        [GESTATION_ITEM],
    )
    assert not verdict
    assert verdict.unsupported_numbers == ("45",)


def test_reformatted_numbers_are_not_treated_as_invented():
    """Rejecting an answer for writing 1000 where the corpus wrote 1,000 would
    train everyone to distrust the gate."""
    source = {"id": "x", "answer": "The tank holds 1,000 litres and costs 2.50 per litre."}
    assert check("It holds 1000 litres at 2.5 per litre.", [source])


def test_list_markers_do_not_need_evidence():
    source = {"id": "x", "answer": "Record the animal, then the session, then save."}
    verdict = check("1. Record the animal.\n2. Record the session.\n3. Save.", [source])
    assert verdict, verdict.violations


def test_numbers_the_operator_supplied_are_supported():
    """A figure from the question is the operator's own and needs no corpus."""
    assert check(
        "Going from 18 L to 13 L is a fall of 5 L.",
        [{"id": "x", "answer": "Yield changes are shown per session."}],
        question="My cow gave 18 L yesterday and 13 L today, a drop of 5 L.",
    )


# ---------------------------------------------------------------------------
# Claims the Assistant is structurally incapable of making truthfully
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "answer",
    [
        "Your farm's records show three animals under withdrawal.",
        "I checked your herd and found nothing outstanding.",
        "According to your data, milk is steady.",
        "Looking at your herd, the Milking group is largest.",
    ],
)
def test_claims_of_farm_data_access_are_rejected(answer: str):
    """The Assistant has no database. Any sentence of this shape is false
    before its content is even considered."""
    verdict = check(answer, [WITHDRAWAL_ITEM])
    assert not verdict
    assert any("claims access to farm data" in v for v in verdict.violations)


def test_an_invented_record_identifier_is_rejected():
    verdict = check("Animal TD-014 is still within its withdrawal.", [WITHDRAWAL_ITEM])
    assert not verdict
    assert any("invented record identifiers" in v for v in verdict.violations)


def test_the_reserved_example_namespace_is_permitted():
    """Worked examples are the product's own teaching device and must survive."""
    source = {"id": "x", "answer": "For example EX-MILK-001 shows a missed session."}
    assert check("Take EX-MILK-001 as an example.", [source])


# ---------------------------------------------------------------------------
# Structural rules
# ---------------------------------------------------------------------------


def test_an_empty_answer_is_rejected():
    assert not check("   ", [WITHDRAWAL_ITEM])


def test_an_answer_without_evidence_is_rejected():
    """Nothing retrieved means nothing to be faithful to."""
    verdict = check("Withdrawal periods are important.", [])
    assert not verdict
    assert any("no evidence" in v for v in verdict.violations)


def test_an_overlong_answer_is_rejected():
    source = {"id": "x", "answer": "milk " * 50}
    verdict = check("milk " * (MAX_ANSWER_CHARACTERS // 4), [source])
    assert not verdict
    assert any("over the" in v for v in verdict.violations)


# ---------------------------------------------------------------------------
# The calculation carve-out cannot become a hole
# ---------------------------------------------------------------------------


def test_derived_numbers_are_allowed_only_for_calculations():
    answer = "18 L falling to 13 L is a drop of 27.8 percent."
    question = "My cow gave 18 L yesterday and 13 L today. What percentage drop is that?"

    assert not check(answer, [], question=question), (
        "without the carve-out an unsupported result must be refused"
    )
    assert check(answer, [], question=question, allow_derived_numbers=True)


def test_the_carve_out_does_not_permit_other_fabrication():
    """Arithmetic freedom is not licence to invent a record or claim access."""
    for answer in [
        "Cow TD-001 fell 27.8 percent.",
        "Your farm's records show a 27.8 percent drop.",
    ]:
        assert not check(answer, [], question="18 and 13", allow_derived_numbers=True)


# ---------------------------------------------------------------------------
# The stub model, fabricating on demand
# ---------------------------------------------------------------------------


class FabricatingModel:
    """Returns whatever it was told to return, so the gate can be tested
    against behaviour a real model only exhibits unpredictably."""

    def __init__(self, text: str) -> None:
        self.text = text

    def generate(self, prompt: str, **kwargs) -> str:
        return self.text


@pytest.mark.parametrize(
    "fabrication",
    [
        "The withdrawal period is 96 hours.",
        "Withdrawal lasts 7 days for most antibiotics.",
        "Your records show 4 animals withdrawn.",
        "Animal AB-77 is withdrawn until Tuesday.",
    ],
)
def test_every_fabrication_the_stub_produces_is_withheld(fabrication: str):
    model = FabricatingModel(fabrication)
    produced = model.generate("irrelevant")
    verdict = check(produced, [WITHDRAWAL_ITEM])
    assert not verdict, f"the gate let through: {produced!r}"
    assert REJECTED_TEXT, "a rejection must have something to show the operator"


def test_a_faithful_restatement_passes():
    """The gate must not reject everything. A model that restates the evidence
    accurately is the whole point of having one."""
    model = FabricatingModel(
        "A withdrawal period is the interval after treatment during which milk "
        "must not enter the tank. DairyOS stores an explicit start and end time "
        "rather than assuming a duration."
    )
    assert check(model.generate("irrelevant"), [WITHDRAWAL_ITEM])


def test_number_extraction_ignores_markers_but_not_claims():
    assert numbers_in("1. Wait 35 days") == {"35"}
    assert numbers_in("Wait 35 days") == {"35"}

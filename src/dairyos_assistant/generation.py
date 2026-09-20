"""Turning retrieved evidence into an answer, and refusing to ship a bad one.

The prompt is built to make fabrication less likely; the gate in
``grounding.py`` is what makes it harmless when it happens anyway. The order
matters, and so does the fact that both exist. A prompt alone is a request, and
a small model under pressure to be helpful will fill a gap with something
plausible. The gate is not a request.

Generation is deliberately narrow. The model is asked to restate the evidence
in plain words for an operator, not to advise, not to add context it knows from
training, and not to reason beyond what it was handed. Anything it adds from
its own weights is exactly what the gate is looking for.
"""

from __future__ import annotations

from typing import Any, Sequence

from dairyos_assistant.grounding import REJECTED_TEXT, Verdict, check
from dairyos_assistant.model import ModelProvider, ModelUnavailable

SYSTEM_RULES = """You are the DairyOS Assistant. You teach a dairy farm operator how DairyOS works.

Rules you must follow exactly:
1. Answer only from the REFERENCE material below. It is the sole source of truth.
2. Never state a number, a duration, a threshold or a date that does not appear in the REFERENCE.
3. You have no access to this farm's records. Never claim to have looked at them.
4. Never invent an animal, a tag, a batch or a transaction identifier.
5. If the REFERENCE does not cover the question, say plainly that you do not know.
6. Reason over the reference instead of merely copying the first matching item.
7. For multi-part questions, answer each part and connect the relevant facts.
8. Distinguish an explicit reference fact from a conclusion that follows directly
   from the reference. Do not fill gaps with general model knowledge.
9. When references disagree or contain a known deviation, name the distinction
   and state which rule applies; never silently blend them.
10. Write plain, direct prose for a working farmer. Give the answer first, then
    a short "Why" or "What to do" explanation when useful. No sign-off.
"""

MAX_REFERENCE_CHARACTERS = 6000

# Fields worth putting in front of the model, in the order an explanation wants
# them. Audit and review metadata is deliberately absent: it is not teaching
# material and a number in it must never be repeated as guidance.
REFERENCE_FIELDS = ("title", "answer", "explanation", "scenario", "exceptions", "correction_path")


def _render_item(item: dict[str, Any]) -> str:
    lines = [f"[{item.get('id', 'unknown')}]"]
    for name in REFERENCE_FIELDS:
        value = item.get(name)
        if value is None or value == "":
            continue
        if isinstance(value, dict):
            rendered = "; ".join(f"{k}: {v}" for k, v in value.items() if v)
        elif isinstance(value, (list, tuple)):
            rendered = "; ".join(str(v) for v in value if v)
        else:
            rendered = str(value)
        lines.append(f"{name}: {rendered}")
    return "\n".join(lines)


def build_prompt(question: str, sources: Sequence[dict[str, Any]]) -> str:
    reference = "\n\n".join(_render_item(item) for item in sources)
    if len(reference) > MAX_REFERENCE_CHARACTERS:
        # Truncating at an item boundary rather than mid-sentence, so the model
        # is never handed half a rule and asked to complete it.
        kept: list[str] = []
        budget = MAX_REFERENCE_CHARACTERS
        for item in sources:
            rendered = _render_item(item)
            if len(rendered) > budget:
                break
            kept.append(rendered)
            budget -= len(rendered)
        reference = "\n\n".join(kept)
    return (
        f"{SYSTEM_RULES}\n"
        f"REFERENCE:\n{reference}\n\n"
        f"Question: {question.strip()}\n"
        f"Reasoning task: identify the applicable facts, relate them to the\n"
        f"question, and produce a concise operator-facing conclusion. Do not\n"
        f"show private chain-of-thought or invent facts.\n"
        f"Answer:"
    )


def generate_answer(
    provider: ModelProvider,
    question: str,
    sources: Sequence[dict[str, Any]],
    *,
    allow_derived_numbers: bool = False,
) -> tuple[str | None, Verdict | None, str | None]:
    """Produce a grounded answer, or nothing at all.

    Returns ``(answer, verdict, failure)``. Exactly one of ``answer`` and
    ``failure`` is set. A model that is unreachable, a model that returns
    nothing, and a model whose answer fails the gate are three different
    situations, and each is reported as itself rather than flattened into a
    generic apology.
    """
    try:
        raw = provider.generate(build_prompt(question, sources))
    except ModelUnavailable as exc:
        return None, None, f"model unavailable: {exc}"

    verdict = check(
        raw,
        list(sources),
        question=question,
        allow_derived_numbers=allow_derived_numbers,
    )
    if not verdict.ok:
        return None, verdict, REJECTED_TEXT
    return raw, verdict, None


GENERAL_SYSTEM_RULES = """You are the optional local general-purpose assistant.
Answer the user's ordinary question clearly and briefly.
You are not DairyOS capability authority, you cannot access Farm records, and
you must not imply that a general answer describes current DairyOS behavior.
Operators may use short, misspelled, incomplete, or vague wording. Infer the
most likely intent when it is safe, explain the likely next step, and ask one
focused follow-up question when the missing detail changes the answer.
For medical, veterinary, legal, or safety-sensitive matters, provide general
educational information and recommend an appropriately qualified professional.
Do not claim to have inspected files, databases, devices, or live systems.
"""


def generate_general_answer(
    provider: ModelProvider,
    question: str,
    context: Sequence[dict[str, Any]] = (),
) -> tuple[str | None, str | None]:
    """Use the local model for ordinary questions outside the approved KB.

    This route is intentionally separate from ``generate_answer``: general
    answers must not be presented as DairyOS-grounded answers, while the same
    model may still be used for both routes. The Farm-data firewall runs before
    this function is reachable.
    """
    related = ""
    if context:
        related = (
            "\n\nRELATED APPROVED DAIRYOS MATERIAL (not necessarily a direct answer):\n"
            + "\n\n".join(_render_item(item) for item in context)
        )
    prompt = f"{GENERAL_SYSTEM_RULES}{related}\n\nQuestion: {question.strip()}\nAnswer:"
    try:
        answer = provider.generate(prompt)
    except ModelUnavailable as exc:
        return None, f"model unavailable: {exc}"
    answer = answer.strip()
    if not answer:
        return None, "general model returned no content"
    return answer, None

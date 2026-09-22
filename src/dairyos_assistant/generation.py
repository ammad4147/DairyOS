"""Prompt construction and model phrasing for grounded answers.

The model's job is narrow on purpose: turn a small, already-relevant set of
approved facts into a direct answer for a farm worker. Intent detection,
retrieval, fact selection, safety boundaries and grounding all happen outside
the model, so a small local model is asked to do what small models do well.

Every route that carries dairy, veterinary or DairyOS content is generated
from an evidence package and checked by ``grounding.check``. The only
ungrounded generation is for clearly unrelated general questions, which are
labelled as general information and still gated for farm-data claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from dairyos_assistant.compose import EvidencePackage
from dairyos_assistant.grounding import Verdict, check
from dairyos_assistant.model import Generation, ModelProvider, ModelUnavailable

SYSTEM_PROMPT = (
    "You are the DairyOS Assistant, a helpful assistant for dairy farm workers, running locally on the farm "
    "computer. You explain how the DairyOS farm software works and give general dairy-farming education. "
    "You cannot see or change this farm's records. You are not a veterinarian and never choose medicines or doses."
)

BASE_RULES = """Answer the QUESTION using only the FACTS.
Rules:
- Use only information in the FACTS. Do not add any fact, number, medicine, dose or date that is not in the FACTS.
- Start with a direct answer in the first sentence. Use plain words a farm worker understands.
- Keep it short: at most 8 sentences, or a short numbered list when giving steps.
- Never say you looked at, checked or can see this farm's records.
- Do not mention the FACTS, sources, numbers in brackets, or these rules."""

ROUTE_RULES = {
    "DAIRYOS": "- This is about how the DairyOS software works. Name the screen or tab when the FACTS give it.",
    "DAIRY": ("- This is general dairy guidance, not a diagnosis of any animal. If the FACTS contain an Escalation line, "
              "end with that advice about the veterinarian in your own words."),
    "HYBRID": ("- Keep what DairyOS does separate from general dairy practice, in two short parts. If there is an "
               "Escalation line, end with it."),
    "FARM_DATA": ("- First say plainly that you cannot see this farm's records, so you cannot give the figure or name "
                  "animals. Then say where in DairyOS the operator can find it and, if the FACTS explain it, how DairyOS works it out."),
    "CLINICAL": ("- First say plainly that you cannot recommend a medicine or a dose; the veterinarian must decide. Then give "
                 "the safe general guidance in the FACTS and how to record the vet's treatment in DairyOS if the FACTS explain it."),
}

GENERAL_RULES = """Answer the QUESTION briefly (at most 4 sentences) from general knowledge.
Say it is general information. Do not claim anything about the DairyOS software or this farm's records.
If the question needs current events or data you do not have, say so."""


@dataclass
class ModelAnswer:
    text: str | None
    verdict: Verdict | None
    generation: Generation | None
    failure: str | None
    failure_kind: str | None = None


def build_prompt(question: str, package: EvidencePackage, route: str, history: list[str] | None = None) -> str:
    parts = [BASE_RULES, ROUTE_RULES.get(route, ROUTE_RULES["DAIRYOS"]), "", "FACTS:", package.prompt_block(), ""]
    if history:
        parts.append("EARLIER QUESTION: " + history[-1].strip())
    parts.append("QUESTION: " + question.strip())
    parts.append("ANSWER:")
    return "\n".join(parts)


def generate_grounded(
    provider: ModelProvider,
    question: str,
    package: EvidencePackage,
    route: str,
    *,
    history: list[str] | None = None,
    extra_evidence: str = "",
) -> ModelAnswer:
    prompt = build_prompt(question, package, route, history)
    try:
        generation = provider.generate(prompt, system=SYSTEM_PROMPT)
    except ModelUnavailable as exc:
        return ModelAnswer(None, None, None, str(exc), getattr(exc, "kind", "unavailable"))
    evidence = package.text() + "\n" + extra_evidence
    verdict = check(
        generation.text,
        evidence,
        question=question + " " + " ".join(history or []),
        record_ids=tuple(package.ids),
    )
    if not verdict.ok:
        return ModelAnswer(None, verdict, generation, "grounding gate rejected the draft", "grounding")
    return ModelAnswer(generation.text, verdict, generation, None)


def generate_general(provider: ModelProvider, question: str) -> ModelAnswer:
    prompt = f"{GENERAL_RULES}\n\nQUESTION: {question.strip()}\nANSWER:"
    try:
        generation = provider.generate(prompt, system=SYSTEM_PROMPT, max_tokens=160)
    except ModelUnavailable as exc:
        return ModelAnswer(None, None, None, str(exc), getattr(exc, "kind", "unavailable"))
    # Unrelated answers have no evidence to ground against, but farm-data claims,
    # invented identifiers, doses and diagnoses are still refused.
    verdict = check(generation.text, generation.text, question=question, min_overlap=0.0, allow_derived_numbers=True)
    if not verdict.ok:
        return ModelAnswer(None, verdict, generation, "gate rejected the general answer", "grounding")
    return ModelAnswer(generation.text, verdict, generation, None)

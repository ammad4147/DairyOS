"""The Assistant process: one question in, one grounded response out.

This module is the entry point of the separately frozen Assistant executable.
It talks to DairyOS over standard input and output (one JSON object per line),
opens no listening socket, imports nothing from ``dairyos`` and can reach only
a loopback model server. Those properties are asserted by the boundary and
packaging suites.

Pipeline for every question::

    normalise -> classify intent -> retrieve (hybrid lexical, collection prior,
    conversation context, relation expansion) -> evidence package (claim-sized
    facts) -> route decision -> model phrasing (optional) -> grounding gate ->
    deterministic composed fallback -> response with evidence and trace

The farm-data boundary is structural: the Assistant has no farm data, so a
request for it is answered with where DairyOS shows the figure and how DairyOS
calculates it, never with a figure. Clinical requests for medicines or doses
are answered with safe education and a veterinary referral.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TextIO

from dairyos_assistant import __version__
from dairyos_assistant.compose import EvidenceItem, EvidencePackage, build_package, compose, select_facts
from dairyos_assistant.generation import generate_general, generate_grounded
from dairyos_assistant.intent import Intent, classify
from dairyos_assistant.model import LlamaServerProvider, ModelProvider, NullProvider, Timeouts
from dairyos_assistant.policy import classify as policy_classify
from dairyos_assistant.retrieval import Hit, KnowledgeIndex

CORPUS_DIRNAME = "assistant-knowledge"
PROTOCOL_VERSION = 2
EVIDENCE_LIMIT = 5

# Retrieval confidence below which a dairy or DairyOS question is treated as not
# covered. Tuned on the development split only.
NOT_COVERED_SCORE = 3.0

_FOLLOW_UP = re.compile(
    r"^\s*(?:and|also|what about|how about|then|so|but|when is it|where is it|is it|does it|do they|what should i look for first|"
    r"why would it|and with|and the|what level|where do i record it|how do i record them|is there)\b|\b(?:it|that|this|them|they|her|his|those)\b",
    re.I,
)
_HOWTO = re.compile(r"\b(?:how (?:do|can|should) i|where (?:do|can|should) i|how to|steps|record|enter|add|entry|kaise|kahan)\b", re.I)
_CALC = re.compile(r"\b(?:calculat\w*|formula|worked out|how is .{0,30} (?:decided|determined|counted))\b", re.I)
_FLOW = re.compile(r"\b(?:where does .{0,30} go|goes? where|flow|what happens (?:after|when|to)|affect\w*|connect\w*|link\w* (?:to|with)|reach\w*)\b", re.I)


def kind_prior_for(question: str) -> dict[str, float]:
    prior: dict[str, float] = {}
    if _HOWTO.search(question):
        prior["HOWTO"] = 1.2
    if _CALC.search(question):
        prior["CALCULATION"] = 1.2
    if _FLOW.search(question):
        prior["DATA_FLOW"] = 1.25
    return prior

BOUNDARY_ID = "assistant.farm-data-boundary"
MEDICINE_ID = "dairy.medicine.boundary"
ABOUT_ID = "assistant.about"

NOT_COVERED_TEXT = (
    "I don't have reliable knowledge on that yet, so I won't guess. I can explain how DairyOS works (Milk, Feed/TMR, "
    "Animals, Breeding, Health, Vaccination, Finance, COP, Dashboard, Reports, Settings) and give general dairy guidance "
    "on calves, cows, milk, feeding, breeding and animal health. Try asking with the animal, stage, sign or screen you mean."
)
HEALTH_NOT_COVERED = (
    " If an animal is unwell, check its temperature, appetite, breathing, manure and milk, keep it separated if it could "
    "be infectious, and contact your veterinarian."
)
OUT_OF_SCOPE_TEXT = (
    "That is outside what I cover. I explain how DairyOS works and give general dairy-farming guidance; I can't help "
    "reliably with unrelated topics."
)
FARM_DATA_LEAD = (
    "I can't see this farm's records, so I can't give you that figure or tell you which animals it applies to. "
    "Here is where DairyOS shows it and how DairyOS works it out."
)
CLINICAL_LEAD = (
    "I can't recommend a medicine, a dose or a withdrawal time; that has to come from your veterinarian and the product "
    "label. Here is the safe general guidance."
)
INJECTION_TEXT = (
    "I can't do that. I have no access to this farm's records, settings or passwords, I can't change or delete anything, "
    "and I can't set my rules aside. I can explain how DairyOS works and where to find or record information yourself."
)
PASSWORD_TEXT = (
    "I can't see or share passwords. If the DairyOS administrator password is lost, the administrator can recover it "
    "with the saved one-time recovery code on the DairyOS computer (System Settings > Navigation Visibility > Recover Password)."
)
META_TEXT = (
    "Hello. I'm the DairyOS Assistant. I can explain how DairyOS works (for example how COP is calculated, where milk "
    "goes after you record it, or what happens after calving) and give general dairy guidance (calves, fresh cows, "
    "mastitis, feeding, breeding). I can't see your farm's records, and medicines and doses are for your veterinarian."
)


def corpus_root() -> Path:
    """Where the knowledge corpus lives, frozen or from source."""
    candidates: list[Path] = []
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        candidates.append(Path(bundled) / CORPUS_DIRNAME)
    here = Path(__file__).resolve()
    candidates.append(here.parents[2] / "docs" / CORPUS_DIRNAME)
    candidates.append(Path.cwd() / "docs" / CORPUS_DIRNAME)
    for candidate in candidates:
        if (candidate / "corpus.json").is_file():
            return candidate
    return candidates[-1]


def provider_from_url(url: str | None, *, timeout: float | None = None, timeouts: dict | None = None) -> ModelProvider:
    if not url:
        return NullProvider()
    if timeouts:
        return LlamaServerProvider(base_url=url, timeouts=Timeouts.from_mapping(timeouts))
    return LlamaServerProvider(base_url=url, timeout=timeout) if timeout else LlamaServerProvider(base_url=url)


def _evidence_rows(hits: list[Hit], used: set[str]) -> list[dict[str, Any]]:
    rows = []
    for hit in hits:
        record = hit.record
        review = record.get("review") or {}
        provenance = record.get("provenance") or []
        rows.append({
            "id": hit.id,
            "title": record.get("title"),
            "collection": record.get("collection"),
            "domain": record.get("domain"),
            "kind": record.get("kind"),
            "score": hit.score,
            "matched_terms": list(hit.matched_terms),
            "via": hit.via,
            "used": hit.id in used,
            "review_status": review.get("status"),
            "freshness": record.get("freshness"),
            "sources": [p.get("publisher") for p in provenance if isinstance(p, dict)][:3],
            "unreviewed": review.get("status") not in {"VET_REVIEWED", "ENGINEERING_VERIFIED", "OWNER_CONFIRMED"},
        })
    return rows


class Assistant:
    def __init__(self, index: KnowledgeIndex | None = None, provider: ModelProvider | None = None) -> None:
        self.index = index if index is not None else KnowledgeIndex.load(corpus_root())
        self.provider = provider if provider is not None else NullProvider()

    # ------------------------------------------------------------------
    def _model_ready(self) -> bool:
        health = getattr(self.provider, "health", None)
        if isinstance(self.provider, NullProvider):
            return False
        return bool(health()) if callable(health) else True

    def _context(self, question: str, history: list[dict] | None):
        if not history:
            return [], [], []
        previous = history[-1]
        prev_question = str(previous.get("question") or "")
        is_follow_up = bool(_FOLLOW_UP.search(question)) or len(self.index.normaliser.normalise(question).tokens) <= 3
        if not is_follow_up:
            return [], [], []
        prev_terms = self.index.normaliser.normalise(prev_question)
        return prev_terms.tokens + prev_terms.expansions, list(previous.get("records") or []), [prev_question]

    def answer(self, question: str, mode: str | None = None, history: list[dict] | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        trace: dict[str, Any] = {"question": question}
        normalised = self.index.normaliser.normalise(question)
        intent = classify(question, normalised)
        context_terms, context_records, history_questions = self._context(question, history)
        if history_questions and intent.intent in {"AMBIGUOUS", "OUT_OF_SCOPE"}:
            # A bare follow-up inherits the previous question's intent.
            combined = self.index.normaliser.normalise(history_questions[-1] + " " + question)
            intent = classify(history_questions[-1] + " " + question, combined)
        # Follow-ups that are themselves farm-data lookups keep that intent.
        trace.update({
            "normalised": normalised.tokens, "expansions": normalised.expansions, "corrections": normalised.corrections,
            "intent": intent.intent, "intent_confidence": intent.confidence, "signals": intent.signals,
            "scores": {"dairyos": intent.dairyos_score, "dairy": intent.dairy_score},
            "follow_up": bool(history_questions),
        })

        hits = self.index.search(
            normalised,
            limit=EVIDENCE_LIMIT,
            collection_prior=intent.collection_prior(),
            context_terms=context_terms,
            context_records=context_records,
            expand_related=intent.intent in {"DAIRYOS", "HYBRID"},
            kind_prior=kind_prior_for(question),
        )
        trace["retrieval"] = [{"id": h.id, "score": h.score, "via": h.via, "terms": list(h.matched_terms)} for h in hits]
        top_score = hits[0].score if hits else 0.0

        route, lead, package, text, generation = self._route(question, normalised, intent, hits, top_score)
        stage = "COMPOSED"
        model_error = None
        verdict = None
        gen_meta = None
        final_text = text
        used_ids: set[str] = set(package.ids) if package else set()

        if route in {"DAIRYOS", "DAIRY", "HYBRID", "FARM_DATA", "CLINICAL", "AMBIGUOUS"} and package and package.items:
            composed = compose(package, question_is_howto=bool(_HOWTO.search(question)), lead=lead)
            final_text = composed
            # The packaged local model is an optional phrasing aid, not an
            # authority.  Its short-model drafts can omit approved workflow
            # steps even when they pass lexical grounding.  Production uses
            # the deterministic approved composition; injected/scripted
            # providers remain available for tests and controlled evaluation.
            model_allowed = not isinstance(self.provider, LlamaServerProvider)
            if route not in {"AMBIGUOUS"} and model_allowed and self._model_ready():
                model_route = route if route != "AMBIGUOUS" else "DAIRYOS"
                result = generate_grounded(self.provider, question, package, model_route, history=history_questions,
                                           extra_evidence=lead or "")
                verdict = result.verdict
                if result.generation:
                    gen_meta = {
                        "ttft_s": result.generation.ttft_s, "total_s": result.generation.total_s,
                        "tokens": result.generation.tokens, "tokens_per_s": result.generation.tokens_per_s,
                        "prompt_tokens": result.generation.prompt_tokens,
                    }
                if result.text:
                    body = result.text
                    already_bounded = re.search(
                        r"can(?:no|')t (?:see|recommend|give)|cannot (?:see|recommend|give)|no access", body, re.I
                    )
                    if lead and route in {"FARM_DATA", "CLINICAL"} and not already_bounded:
                        body = lead.split(". Here is")[0] + ".\n\n" + body
                    final_text = body
                    stage = "ANSWERED"
                    generation = "MODEL"
                else:
                    model_error = result.failure
                    trace["model_failure_kind"] = result.failure_kind
                    generation = "COMPOSED"
            else:
                generation = "COMPOSED"
                if route != "AMBIGUOUS":
                    model_error = "model unavailable"
        elif route == "OUT_OF_SCOPE":
            stage = "OUT_OF_SCOPE"
            if self._model_ready():
                result = generate_general(self.provider, question)
                if result.text:
                    final_text = "General information (not from DairyOS knowledge): " + result.text
                    stage = "GENERAL_ANSWERED"
                    generation = "MODEL_GENERAL"
                else:
                    model_error = result.failure
        else:
            stage = {"FARM_DATA": "BOUNDARY", "INJECTION": "BOUNDARY", "META": "META", "NOT_COVERED": "NOT_COVERED",
                     "CLINICAL": "BOUNDARY"}.get(route, "COMPOSED")

        if route in {"FARM_DATA", "CLINICAL", "INJECTION"} and stage == "COMPOSED":
            stage = "BOUNDARY"
        if route == "NOT_COVERED":
            stage = "NOT_COVERED"
        if route == "AMBIGUOUS":
            stage = "CLARIFY"

        label = {
            "DAIRYOS": "DairyOS", "DAIRY": "Dairy guidance", "HYBRID": "DairyOS and dairy guidance",
            "FARM_DATA": "Farm records not accessible", "CLINICAL": "Veterinary decision", "INJECTION": "Not permitted",
            "OUT_OF_SCOPE": "Outside DairyOS", "META": "DairyOS Assistant", "NOT_COVERED": "Not covered",
            "AMBIGUOUS": "Please clarify",
        }.get(route, route)
        follow_ups = self._follow_ups(hits, used_ids)
        hit_ids = {h.id for h in hits}
        package_hits = [
            Hit(record=item.record, score=0.0, lexical=0.0, matched_terms=(), via="boundary")
            for item in (package.items if package else [])
            if item.id not in hit_ids
        ]
        ordered = package_hits + [h for h in hits if h.id in used_ids] + [h for h in hits if h.id not in used_ids]
        evidence = _evidence_rows(ordered, used_ids)
        elapsed = time.perf_counter() - started
        trace.update({
            "route": route, "stage": stage, "generation": generation, "evidence_ids": sorted(used_ids),
            "evidence_text": package.text() + "\n" + (lead or "") if package else (lead or ""),
            "grounding": {"ok": verdict.ok, "violations": list(verdict.violations), "overlap": verdict.overlap} if verdict else None,
            "model": gen_meta, "model_error": model_error, "latency_s": round(elapsed, 3),
        })
        legacy_policy = policy_classify(question)
        dairy_used = any((self.index.get(i) or {}).get("collection") == "dairy" for i in used_ids)
        return {
            "decision": legacy_policy.decision.value,
            "intent": intent.intent,
            "route": route,
            "stage": stage,
            "label": label,
            "text": final_text,
            "answer": final_text if stage in {"ANSWERED", "COMPOSED", "BOUNDARY", "GENERAL_ANSWERED", "CLARIFY", "META"} else None,
            "generation": generation,
            "evidence": evidence,
            "follow_ups": follow_ups,
            "unreviewed": any(r["unreviewed"] and r["used"] for r in evidence),
            "general_knowledge": route in {"DAIRY", "OUT_OF_SCOPE"} or dairy_used,
            "verbatim": False,
            "model_error": model_error,
            "operational_data_access": "NONE",
            "trace": trace,
        }

    # ------------------------------------------------------------------
    def _boundary_package(self, hits: list[Hit], normalised, extra_ids: Iterable[str], exclude: set[str]) -> EvidencePackage:
        package = EvidencePackage()
        for record_id in extra_ids:
            record = self.index.get(record_id)
            if record is not None:
                package.items.append(EvidenceItem(record, select_facts(record, normalised, 3), [], "boundary"))
        for hit in hits:
            if len(package.items) >= 4:
                break
            if hit.id in exclude or hit.id in package.ids:
                continue
            package.items.append(EvidenceItem(hit.record, select_facts(hit.record, normalised, 3),
                                              [], "secondary" if package.items else "primary"))
        return package

    def _route(self, question: str, normalised, intent: Intent, hits: list[Hit], top_score: float):
        route = intent.intent
        if route == "META":
            about = self.index.get(ABOUT_ID)
            package = EvidencePackage([EvidenceItem(about, [], [], "primary")]) if about else EvidencePackage()
            return "META", None, package, META_TEXT, "FIXED"
        if route == "INJECTION":
            text = PASSWORD_TEXT if re.search(r"password", question, re.I) else INJECTION_TEXT
            package = EvidencePackage()
            if intent.farm_data or re.search(r"\b(?:milk|cow|finance|records?|animals?)\b", question, re.I):
                boundary = self.index.get(BOUNDARY_ID)
                if boundary:
                    package.items.append(EvidenceItem(boundary, select_facts(boundary, normalised, 2), [], "boundary"))
                    text += "\n\n" + "\n".join(f"- {f}" for f in package.items[0].facts)
            return "INJECTION", None, package, text, "FIXED"
        if route == "FARM_DATA":
            # Primary evidence: where DairyOS shows it; then how it is calculated; then any health guidance.
            content = [h for h in hits if h.id != BOUNDARY_ID and h.record.get("collection") == "dairyos"][:1]
            dairy = [h for h in hits if h.record.get("collection") == "dairy"][:1] if intent.health else []
            package = self._boundary_package(content + dairy, normalised, [BOUNDARY_ID], set())
            return "FARM_DATA", FARM_DATA_LEAD, package, None, None
        if route == "CLINICAL":
            dairy = [h for h in hits if h.record.get("collection") == "dairy" and h.id != MEDICINE_ID][:1]
            dairyos = [h for h in hits if h.id in {"health.treatment", "health.withdrawal"}][:1]
            package = self._boundary_package(dairy + dairyos, normalised, [MEDICINE_ID], set())
            return "CLINICAL", CLINICAL_LEAD, package, None, None
        if route == "OUT_OF_SCOPE":
            # Only override the classifier when the match is substantive: several
            # distinct query terms, not one shared word ("capital").
            if hits and top_score >= NOT_COVERED_SCORE * 1.5 and len(hits[0].matched_terms) >= 2:
                route = "DAIRYOS" if hits[0].collection == "dairyos" else "DAIRY"
            else:
                return "OUT_OF_SCOPE", None, EvidencePackage(), OUT_OF_SCOPE_TEXT, "FIXED"
        if not hits or top_score < NOT_COVERED_SCORE:
            text = NOT_COVERED_TEXT + (HEALTH_NOT_COVERED if intent.health else "")
            return "NOT_COVERED", None, EvidencePackage(), text, "FIXED"
        package = build_package(hits, normalised)
        if route == "AMBIGUOUS":
            second = hits[1].score if len(hits) > 1 else 0.0
            if top_score >= 1.6 * second:
                # A bare but specific term ("COP?", "BVD"): answer it, and offer neighbours.
                route = "DAIRYOS" if hits[0].collection == "dairyos" else "DAIRY"
            else:
                titles = [h.record.get("title") for h in hits[1:4]]
                text = compose(package) + ("\n\nDid you mean: " + "; ".join(t for t in titles if t) + "?" if titles else "")
                return "AMBIGUOUS", None, package, text, "COMPOSED"
        # The route follows the evidence actually used: the primary record's
        # collection, or HYBRID when strong evidence from both is in play.
        primary = package.items[0].record.get("collection")
        others = {item.record.get("collection") for item in package.items[1:] if item.role != "boundary"}
        route = "DAIRYOS" if primary == "dairyos" else "DAIRY"
        if others - {primary} and intent.intent == "HYBRID":
            route = "HYBRID"
        return route, None, package, None, None

    def _follow_ups(self, hits: list[Hit], used: set[str]) -> list[str]:
        suggestions = []
        for hit in hits:
            if hit.id in used or hit.id in {BOUNDARY_ID, ABOUT_ID}:
                continue
            questions = hit.record.get("questions") or []
            if questions:
                suggestions.append(str(questions[0]))
            if len(suggestions) >= 3:
                break
        return suggestions

    def status(self) -> dict[str, Any]:
        report = dict(self.index.status_report())
        report["assistant_version"] = __version__
        report["protocol_version"] = PROTOCOL_VERSION
        report["corpus_root"] = str(corpus_root())
        report["operational_data_access"] = "NONE"
        report["model_configured"] = not isinstance(self.provider, NullProvider)
        report["model_ready"] = self._model_ready()
        return report


def handle(request: dict[str, Any], assistant: Assistant) -> dict[str, Any]:
    kind = str(request.get("type") or "ask").strip().lower()
    if kind == "status":
        return {"ok": True, "type": "status", "status": assistant.status()}
    if kind == "ask":
        question = request.get("question")
        if not isinstance(question, str) or not question.strip():
            return {"ok": False, "type": "ask", "error": "question is required"}
        history = request.get("history") or []
        if not isinstance(history, list):
            return {"ok": False, "type": "ask", "error": "history must be a list"}
        clean_history = []
        for turn in history[-3:]:
            if isinstance(turn, dict) and isinstance(turn.get("question"), str):
                clean_history.append({
                    "question": turn["question"][:600],
                    "records": [str(r) for r in (turn.get("records") or [])][:5],
                })
        reply = assistant.answer(question, request.get("mode"), clean_history)
        if not request.get("diagnostics"):
            reply = {k: v for k, v in reply.items() if k != "trace"}
        return {"ok": True, "type": "ask", **reply}
    return {"ok": False, "type": kind, "error": f"unknown request type: {kind!r}"}


def serve(stdin: TextIO | Iterable[str] | None = None, stdout: TextIO | None = None, assistant: Assistant | None = None) -> None:
    """Read requests until the input closes; a bad line gets an error, never a crash."""
    source = sys.stdin if stdin is None else stdin
    sink = sys.stdout if stdout is None else stdout
    if source is None or sink is None:
        print("DairyOS Assistant: no standard input or output; it must be started by DairyOS.", file=sys.stderr)
        return
    worker = assistant if assistant is not None else Assistant()
    for line in source:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response: dict[str, Any] = {"ok": False, "error": f"invalid JSON: {exc}"}
        else:
            if not isinstance(request, dict):
                response = {"ok": False, "error": "request must be a JSON object"}
            else:
                try:
                    response = handle(request, worker)
                except Exception as exc:  # noqa: BLE001 - reported, never raised at the backend
                    response = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        try:
            sink.write(json.dumps(response, ensure_ascii=False) + "\n")
            sink.flush()
        except (BrokenPipeError, OSError) as exc:
            if isinstance(exc, OSError) and getattr(exc, "errno", None) not in {22, 9}:
                print(f"DairyOS Assistant: output stream failed: {exc}", file=sys.stderr)
            return


def _arg(argv: list[str], name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None


def _provider_from(argv: list[str]) -> ModelProvider:
    url = _arg(argv, "--model-url")
    timeouts = _arg(argv, "--model-timeouts")
    return provider_from_url(url, timeouts=json.loads(timeouts) if timeouts else None)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    provider = _provider_from(argv)
    if "--status" in argv:
        print(json.dumps(Assistant(provider=provider).status(), indent=2))
        return 0
    question = _arg(argv, "--diagnose")
    if question:
        reply = Assistant(provider=provider).answer(question)
        print(json.dumps(reply, indent=2, ensure_ascii=False))
        return 0
    serve(assistant=Assistant(provider=provider))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

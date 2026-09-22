"""Run the Assistant gold benchmark and write a scored report.

Examples (repository root)::

    python tools/assistant_eval.py --out bench.json                      # V2, no model (composed answers)
    python tools/assistant_eval.py --model-url http://127.0.0.1:8080     # V2 with a running llama-server
    python tools/assistant_eval.py --legacy-root ../old --legacy-mode dairyos   # baseline of a legacy checkout

Every question's full trace (route, retrieved records, answer, grounding, latency)
is written so that each failure can be classified as routing, corpus gap,
retrieval, generation, grounding or runtime.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "assistant" / "benchmark"))
import harness  # noqa: E402

# Generous mapping of legacy corpus ids onto the V2 ids a gold question requires,
# so the baseline is credited whenever it retrieved equivalent knowledge.
LEGACY_MAP = {
    "breeding.pregnancy": ["breeding.pd", "breeding.expected-calving"],
    "breeding.ai": ["breeding.ai", "breeding.semen"],
    "breeding.abortion-or-loss": ["breeding.pregnancy-loss"],
    "breeding.dry-off": ["animals.dry-off", "breeding.expected-calving"],
    "breeding.chronology": ["breeding.cycle"], "breeding.current-state": ["breeding.cycle"],
    "breeding.event": ["breeding.cycle"], "breeding.calving": ["breeding.calving", "animals.calf-id"],
    "breeding.post-calving-return": ["breeding.post-calving-return", "breeding.vwp"],
    "animals.groups": ["animals.categories"], "animals.identity-and-passport": ["animals.passport"],
    "animals.lifecycle": ["animals.lifecycle", "animals.categories"],
    "health.treatment-withdrawal": ["health.withdrawal"], "health.resolution": ["health.mark-healthy"],
    "health.follow-up-resolution": ["health.mark-healthy", "health.follow-up"],
    "health.observation-triage": ["health.observation"], "health.summary": ["health.analytics"],
    "health.severity": ["health.treatment"],
    "vaccination.event": ["vaccination.schedule"], "health.vaccination": ["vaccination.schedule"],
    "vaccination.missed-or-reaction": ["vaccination.schedule"],
    "vaccination.programme-design": ["dairy.vaccination.principles"],
    "finance.cost-of-production": ["cop.estimated"], "analytics.period-and-cop": ["cop.estimated", "cop.troubleshooting"],
    "feed.feed-cost-per-litre": ["cop.feed-cost-per-litre"], "feed.formula": ["feed.tmr-tool"],
    "feed.category-cost": ["feed.tmr-cost"], "feed.herd-cost": ["feed.tmr-cost"], "feed.tmr-log": ["feed.daily-snapshot"],
    "feed.ingredients": ["feed.prices", "feed.tmr-tool"], "feed.consumption": ["feed.storage"],
    "revenue.disposition": ["milk.dispositions"], "revenue.non-sale": ["milk.dispositions"],
    "revenue.sale": ["finance.milk-sale"], "revenue.sold-litres": ["milk.saleable"], "revenue.revenue": ["finance.milk-sale"],
    "revenue.receivable": ["finance.payment-status"], "revenue.cash": ["finance.payment-status"],
    "revenue.sale-amendment": ["finance.amendment"], "revenue.void": ["finance.void"],
    "finance.expense-entry": ["finance.financial-entry"], "finance.category": ["finance.expense-category"],
    "finance.profitability": ["finance.running-status"],
    "dashboard.alert-lifecycle": ["dashboard.findings"], "dashboard.acknowledge": ["dashboard.findings"],
    "dashboard.resolution": ["dashboard.findings"], "dashboard.resolve": ["dashboard.findings"],
    "dashboard.decisions": ["dashboard.findings"], "dashboard.cards": ["dashboard.cards"],
    "settings.date-convention": ["settings.operational-date"], "settings.timezone": ["settings.operational-date"],
    "installation.automatic-backup": ["settings.backup"], "installation.verified-recovery": ["settings.backup"],
    "installation.upgrade-and-backup": ["settings.backup"], "settings.zero-state-reset": ["settings.zero-reset"],
    "access.hidden-tabs": ["settings.navigation-visibility"], "settings.tab-visibility": ["settings.navigation-visibility"],
    "analytics.catalog": ["analytics.overview"], "analytics.kpis": ["analytics.overview"], "analytics.exports": ["reports.catalog"],
    "troubleshooting.save-failure": ["support.troubleshooting"], "troubleshooting.missing-data": ["support.troubleshooting"],
    "troubleshooting.stale-view": ["support.troubleshooting"], "troubleshooting.wrong-calculation": ["cop.troubleshooting"],
    "assistant.answer-contract": ["assistant.about"],
    "disease.mastitis": ["dairy.mastitis.signs"], "disease.metritis-endometritis": ["dairy.transition.metritis"],
    "disease.milk-fever": ["dairy.transition.milk-fever"], "disease.ketosis": ["dairy.transition.ketosis"],
    "disease.brd": ["dairy.calf.pneumonia"], "disease.calves-scours": ["dairy.calf.scours-triage", "dairy.calf.scours-causes"],
    "disease.lameness": ["dairy.welfare.lameness"], "disease.bvd": ["dairy.disease.bvd"], "disease.fmd": ["dairy.disease.fmd"],
    "disease.brucellosis": ["dairy.disease.brucellosis"], "disease.heat-stress": ["dairy.welfare.heat-stress"],
    "health.heat-stress": ["dairy.welfare.heat-stress"], "disease.parasites": ["dairy.disease.parasites"],
    "dairy.calves.colostrum-and-scours": ["dairy.calf.colostrum-timing", "dairy.calf.scours-triage"],
    "dairy.transition.close-up-cow": ["dairy.transition.close-up", "dairy.transition.fresh-cow-watch"],
    "dairy.nutrition.tmr-intake": ["dairy.nutrition.intake-drop", "dairy.nutrition.tmr-basics"],
    "dairy.milk-quality.triage": ["dairy.mastitis.signs", "dairy.mastitis.prevention"],
    "dairy.welfare.heat-lameness": ["dairy.welfare.heat-stress", "dairy.welfare.lameness"],
    "dairy.management.daily-review": ["dashboard.cards"],
}


class V2System:
    def __init__(self, model_url: str | None, timeout: float | None):
        sys.path.insert(0, str(ROOT / "src"))
        from dairyos_assistant.service import Assistant, provider_from_url

        self.assistant = Assistant(provider=provider_from_url(model_url, timeout=timeout))

    def ask(self, question: str, history: list[str]) -> dict:
        turns = []
        for previous in history:
            reply = self.assistant.answer(previous, history=turns)
            turns.append({"question": previous, "records": [e["id"] for e in reply.get("evidence", [])]})
        started = time.perf_counter()
        reply = self.assistant.answer(question, history=turns)
        latency = time.perf_counter() - started
        return {
            "text": reply.get("text") or "",
            "route": reply.get("route"),
            "records": [e["id"] for e in reply.get("evidence", [])],
            "evidence_text": reply.get("trace", {}).get("evidence_text", ""),
            "latency_s": latency,
            "model_used": reply.get("generation") == "MODEL",
            "trace": reply.get("trace"),
        }


class LegacySystem:
    def __init__(self, legacy_root: Path, mode: str, model_url: str | None, timeout: float | None):
        sys.path.insert(0, str(legacy_root / "src"))
        for name in list(sys.modules):
            if name.startswith("dairyos_assistant"):
                del sys.modules[name]
        service = importlib.import_module("dairyos_assistant.service")
        model = importlib.import_module("dairyos_assistant.model")
        provider = model.NullProvider()
        if model_url:
            provider = model.LlamaServerProvider(base_url=model_url, **({"timeout": timeout} if timeout else {}))
        self.assistant = service.Assistant(provider=provider)
        self.mode = mode

    def _mode_for(self, expected_route: str) -> str:
        if self.mode == "oracle":
            return "general" if expected_route in {"DAIRY", "CLINICAL_BOUNDARY", "OUT_OF_SCOPE"} else "dairyos"
        return self.mode

    def ask(self, question: str, history: list[str], expected_route: str = "") -> dict:
        started = time.perf_counter()
        reply = self.assistant.answer(question, self._mode_for(expected_route))
        latency = time.perf_counter() - started
        evidence = reply.get("evidence") or []
        ids = []
        for e in evidence:
            for mapped in LEGACY_MAP.get(e["id"], [e["id"]]):
                if mapped not in ids:
                    ids.append(mapped)
        stage = reply.get("stage")
        classes = [e.get("class") for e in evidence]
        if stage == "DAIRYOS_CLARIFICATION":
            route = "CLARIFY"
        elif reply.get("decision") == "REFUSE_OPERATIONAL_DATA":
            route = "FARM_DATA"
        elif not evidence:
            route = "OUT_OF_SCOPE"
        elif classes and all(c == "DAIRY_KNOWLEDGE" for c in classes):
            route = "DAIRY"
        elif "DAIRY_KNOWLEDGE" in classes:
            route = "HYBRID"
        else:
            route = "DAIRYOS"
        evidence_text = " ".join(
            " ".join(str(e.get("item", {}).get(k, "")) for k in ("answer", "explanation")) for e in []
        )
        # Legacy evidence items are not returned to the caller; approximate with the answer's own retrieval.
        try:
            hits = self.assistant.index.search(question, limit=4)
            evidence_text = " ".join(json.dumps(h.item) for h in hits)
        except Exception:  # noqa: BLE001
            pass
        return {
            "text": reply.get("text") or reply.get("answer") or "",
            "route": route,
            "records": ids,
            "evidence_text": evidence_text,
            "latency_s": latency,
            "model_used": stage in {"ANSWERED", "GENERAL_ANSWERED", "GUIDANCE_ANSWERED"},
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model-url")
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--legacy-root", type=Path)
    parser.add_argument("--legacy-mode", default="dairyos", choices=["dairyos", "general", "oracle"])
    parser.add_argument("--split", choices=["dev", "test", "all"], default="all")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--one-per-group", action="store_true", help="sample one phrasing per group (for slow model runs)")
    parser.add_argument("--out", type=Path, default=Path("assistant_eval.json"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    questions = harness.load()
    if args.split != "all":
        questions = [q for q in questions if q.split == args.split]
    if args.one_per_group:
        seen, sampled = set(), []
        for q in questions:
            if q.gid not in seen:
                seen.add(q.gid)
                sampled.append(q)
        questions = sampled
    if args.limit:
        questions = questions[: args.limit]

    if args.legacy_root:
        system = LegacySystem(args.legacy_root, args.legacy_mode, args.model_url, args.timeout)
    else:
        system = V2System(args.model_url, args.timeout)

    scores, rows = [], []
    for index, question in enumerate(questions, 1):
        try:
            if isinstance(system, LegacySystem):
                result = system.ask(question.question, question.history, question.route)
            else:
                result = system.ask(question.question, question.history)
        except Exception as exc:  # noqa: BLE001 - a crash is a scored runtime failure
            result = {"text": "", "route": "ERROR", "records": [], "latency_s": 0.0, "error": repr(exc)}
        s = harness.score(question, result)
        if result.get("error"):
            s.failure_class = "runtime"
        scores.append(s)
        rows.append({"question": question.question, "history": question.history, **asdict(s),
                     "trace": result.get("trace"), "error": result.get("error")})
        if not args.quiet:
            print(f"[{index:3}/{len(questions)}] {s.grade:<11} {s.route_actual:<17} r@5={s.recall_at_5} f={s.fact_recall:.2f} "
                  f"{s.latency_s:5.2f}s {question.qid}: {question.question[:60]}", flush=True)
    summary = harness.summarise(scores)
    args.out.write_text(json.dumps({"summary": summary, "questions": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["overall"], indent=1))
    print("grades:", summary["grades"])
    print("failures:", summary["failure_classes"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

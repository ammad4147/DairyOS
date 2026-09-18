"""The Assistant process: one question in, one grounded response out.

This module is the entry point of the Assistant executable. It exists so that
the Assistant can be frozen separately from DairyOS, with its own dependency
graph, and so the claim that it cannot reach farm data is a property of the
shipped binary rather than of the source tree alone.

**The channel is standard input and standard output, not a socket.** That is a
security decision, not a convenience one. The boundary suite asserts that the
Assistant opens no socket at all, and a process that listens on a port would
make that assertion impossible to keep. The DairyOS backend starts this process
and talks to it over pipes, so the Assistant has no address, nothing can connect
to it, and it can initiate nothing.

The protocol is one JSON object per line in each direction. Standard output
carries protocol only; anything diagnostic goes to standard error, so a stray
print cannot corrupt a response.

**What this does not do yet.** Answer generation arrives at AA-7 with the local
model and the grounding gate. Until then a response carries ``answer: null`` and
``stage: "RETRIEVAL_ONLY"``, and the evidence that was retrieved. Nothing here
composes prose, so nothing here can fabricate it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, TextIO

from dairyos_assistant import __version__
from dairyos_assistant.policy import (
    Decision,
    REFUSAL_TEXT,
    classify,
    is_instructional,
)
from dairyos_assistant.retrieval import (
    NO_EVIDENCE_TEXT,
    KnowledgeIndex,
)

CORPUS_DIRNAME = "assistant-knowledge"

PROTOCOL_VERSION = 1

# How many items of evidence a single answer may rest on. Kept small
# deliberately: an answer assembled from eight loosely related items is how a
# knowledge system starts sounding authoritative about things it has not been
# told.
EVIDENCE_LIMIT = 4


def corpus_root() -> Path:
    """Where the knowledge corpus lives, frozen or from source.

    PyInstaller unpacks bundled data under ``sys._MEIPASS``. Running from a
    checkout, the corpus sits under ``docs/`` at the repository root. Both are
    tried in that order, and the first that exists wins.
    """
    candidates: list[Path] = []
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        candidates.append(Path(bundled) / CORPUS_DIRNAME)
    here = Path(__file__).resolve()
    candidates.append(here.parents[2] / "docs" / CORPUS_DIRNAME)
    candidates.append(Path.cwd() / "docs" / CORPUS_DIRNAME)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    # Returned rather than raised so the process can start and report a
    # missing corpus through the protocol, instead of dying before it can say
    # why. An Assistant that will not start is harder to diagnose on a farm
    # machine than one that starts and says its knowledge is missing.
    return candidates[-1]


class Assistant:
    """Policy, then retrieval. In that order, always."""

    def __init__(self, index: KnowledgeIndex | None = None) -> None:
        self.index = index if index is not None else KnowledgeIndex.load(corpus_root())

    def answer(self, question: str) -> dict[str, Any]:
        verdict = classify(question)

        # The refusal is decided before the corpus is consulted. A question
        # about this farm's records is refused whether or not the knowledge
        # base happens to contain something that looks like a match, because
        # the decision is about what was asked, not about what could be found.
        if verdict.decision is Decision.REFUSE_OPERATIONAL_DATA:
            return {
                "decision": verdict.decision.value,
                "stage": "REFUSED",
                "answer": None,
                "text": REFUSAL_TEXT,
                "reason": verdict.reason,
                "signals": list(verdict.signals),
                "instructional_phrasing": is_instructional(question),
                "evidence": [],
                "unreviewed": False,
            }

        hits = self.index.search(question, limit=EVIDENCE_LIMIT)
        evidence = [
            {
                "id": hit.knowledge_id,
                "title": hit.title,
                "domain": hit.domain,
                "capability": hit.capability,
                "class": hit.item_class,
                "status": hit.status,
                "score": hit.score,
                "matched_terms": list(hit.matched_terms),
                "unreviewed": hit.unreviewed,
            }
            for hit in hits
        ]
        return {
            "decision": verdict.decision.value,
            "stage": "RETRIEVAL_ONLY",
            "answer": None,
            "text": None if evidence else NO_EVIDENCE_TEXT,
            "reason": verdict.reason,
            "signals": list(verdict.signals),
            "evidence": evidence,
            "unreviewed": any(item["unreviewed"] for item in evidence),
        }

    def status(self) -> dict[str, Any]:
        report = dict(self.index.status_report())
        report["assistant_version"] = __version__
        report["protocol_version"] = PROTOCOL_VERSION
        report["corpus_root"] = str(corpus_root())
        report["operational_data_access"] = "NONE"
        return report


def handle(request: dict[str, Any], assistant: Assistant) -> dict[str, Any]:
    kind = str(request.get("type") or "ask").strip().lower()
    if kind == "status":
        return {"ok": True, "type": "status", "status": assistant.status()}
    if kind == "ask":
        question = request.get("question")
        if not isinstance(question, str) or not question.strip():
            return {"ok": False, "type": "ask", "error": "question is required"}
        return {"ok": True, "type": "ask", **assistant.answer(question)}
    return {"ok": False, "type": kind, "error": f"unknown request type: {kind!r}"}


def serve(
    stdin: TextIO | Iterable[str] | None = None,
    stdout: TextIO | None = None,
    assistant: Assistant | None = None,
) -> None:
    """Read requests until the input closes.

    A malformed line is answered with an error and the loop continues, because
    one bad request from the backend should not take the Assistant down and
    leave the operator with a dead panel and no explanation.
    """
    source = sys.stdin if stdin is None else stdin
    sink = sys.stdout if stdout is None else stdout
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
        sink.write(json.dumps(response, ensure_ascii=False) + "\n")
        sink.flush()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--status" in argv:
        print(json.dumps(Assistant().status(), indent=2))
        return 0
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

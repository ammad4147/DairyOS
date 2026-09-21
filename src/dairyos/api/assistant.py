"""DairyOS AI Assistant API.

The Assistant is a knowledge-only subsystem that teaches how DairyOS works. It
runs as a separate process with its own dependency graph and a sanitised
environment, and this router is the only route between it and the application.

The route is deliberately thin. It carries a question across and carries a
response back. It performs no retrieval, consults no corpus, and holds no
model, because every decision the Assistant makes is made on the far side of
the pipe where the operational imports do not exist. Adding judgement here
would move part of the boundary into the process that has database access,
which is the one place it must never live.

This module has no access to DairyOS operational data, repositories, domain
services, operational logs, or farm state, and imports nothing that would give
it any.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from dairyos import assistant_package
from dairyos.knowledge_bridge import bridge, stop_orphaned_assistant_processes

router = APIRouter(prefix="/assistant", tags=["assistant"])


def _stop_assistant_before_activation() -> None:
    bridge.stop()
    stop_orphaned_assistant_processes()

# Long enough for a real question, short enough that the prompt cannot be used
# to push the retrieved evidence out of the model's context.
MAX_QUESTION_CHARACTERS = 600


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARACTERS)

    @field_validator("question")
    @classmethod
    def _must_not_be_only_whitespace(cls, value: str) -> str:
        """``min_length`` counts spaces, so "   " satisfied it and travelled all
        the way to the Assistant as an empty question. Rejected at the boundary
        instead, where the operator gets a clear answer rather than a blank
        one."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be empty")
        return stripped


@router.get("/status")
def assistant_status() -> dict[str, Any]:
    """What the Assistant is, and whether it is ready.

    The two constants below are contractual. They are asserted by
    ``tests/architecture/test_ai_assistant_greenfield_retirement.py`` so that
    the Assistant cannot acquire operational access without a test changing.
    """
    payload: dict[str, Any] = {
        "mode": "KNOWLEDGE_ONLY",
        "operational_data_access": "NONE",
    }
    state = bridge.status()
    payload.update(state)
    payload["package"] = assistant_package.status()
    payload["status"] = "READY" if state.get("running") else "UNAVAILABLE"
    return payload


@router.post("/install")
async def install_assistant(files: list[UploadFile] | None = File(default=None)) -> dict[str, Any]:
    """Install a verified Assistant package selected by the administrator."""
    temporary: Path | None = None
    try:
        if not files:
                result = assistant_package.install(before_activate=_stop_assistant_before_activation)
        else:
            if len(files) != 1:
                raise ValueError("Select one approved .dairyassistant package file.")
            package = files[0]
            if not str(package.filename or "").lower().endswith(assistant_package.SINGLE_FILE_SUFFIX):
                raise ValueError("Selected Assistant package must be a .dairyassistant file.")
            temporary = Path(tempfile.mkdtemp(prefix="dairyos-assistant-upload-"))
            package_path = temporary / "assistant-package.dairyassistant"
            with package_path.open("wb") as handle:
                shutil.copyfileobj(package.file, handle)
            result = assistant_package.install(package_path, before_activate=_stop_assistant_before_activation)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)
    return {"status": "INSTALLED", "package": result}


@router.post("/ask")
def ask_assistant(payload: AssistantQuestion) -> dict[str, Any]:
    response = bridge.ask(payload.question)

    if not response.get("ok"):
        # The Assistant being unavailable is a 503 and says why. It is never
        # answered from this side, because this side has no knowledge to answer
        # from and a plausible-sounding fallback written here would be the
        # exact failure the subsystem exists to prevent.
        raise HTTPException(
            status_code=503,
            detail=response.get("error", "The AI Assistant is unavailable."),
        )

    return {
        "mode": "KNOWLEDGE_ONLY",
        "operational_data_access": "NONE",
        "stage": response.get("stage"),
        "decision": response.get("decision"),
        # What the operator is shown. Never assembled here.
        "text": response.get("text") or response.get("answer"),
        "answer": response.get("answer"),
        "evidence": response.get("evidence", []),
        "unreviewed": bool(response.get("unreviewed")),
        "general_knowledge": bool(response.get("general_knowledge")),
        "related_evidence": bool(response.get("related_evidence")),
        "grounding_note": response.get("grounding_note"),
        "verbatim": bool(response.get("verbatim")),
    }

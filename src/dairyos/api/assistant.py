"""Autonomous, grounded, read-only AI Assistant API."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.assistant.agentic import get_agentic_assistant
from dairyos.assistant.contracts import AssistantResponse

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    role: Literal[
        "Operator",
        "Supervisor",
        "Finance",
        "Veterinary / Health",
        "Technical",
    ] = "Operator"
    conversation_id: str | None = Field(default=None, max_length=120)


@router.post("/ask", response_model=AssistantResponse)
def ask_assistant(payload: AssistantQuestion):
    try:
        return get_agentic_assistant().ask(
            payload.question, payload.role, payload.conversation_id
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/coverage")
def assistant_coverage():
    try:
        from dairyos.assistant.knowledge import GroundedAssistant

        return GroundedAssistant().coverage()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/tools")
def assistant_tools():
    return {
        "assistant_name": "AI Assistant",
        "tools": get_agentic_assistant().registry.schemas(),
    }


@router.get("/data-sources")
def assistant_data_sources():
    from dairyos.assistant.operational import operational_capability_catalog

    return operational_capability_catalog()


@router.delete("/conversations/{conversation_id}")
def reset_conversation(conversation_id: str):
    return {
        "conversation_id": conversation_id,
        "reset": get_agentic_assistant().reset(conversation_id),
    }

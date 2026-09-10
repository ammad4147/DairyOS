"""Question-first, grounded, read-only DairyOS Assistant API."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.assistant.knowledge import GroundedAssistant

router = APIRouter(prefix="/assistant", tags=["DairyOS Assistant"])


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    role: Literal[
        "Operator",
        "Supervisor",
        "Finance",
        "Veterinary / Health",
        "Technical",
    ] = "Operator"


@router.post("/ask")
def ask_assistant(payload: AssistantQuestion):
    try:
        return GroundedAssistant().answer(payload.question, payload.role)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/coverage")
def assistant_coverage():
    try:
        return GroundedAssistant().coverage()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

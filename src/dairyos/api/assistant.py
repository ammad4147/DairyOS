"""DairyOS AI Assistant API retirement boundary.

The former Assistant implementation has been retired.

A new knowledge-only Assistant will be implemented independently.  This
temporary endpoint deliberately has no access to DairyOS operational data,
repositories, domain services, operational logs, or farm state.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/status")
def assistant_status() -> dict[str, str]:
    return {
        "status": "REBUILDING",
        "mode": "KNOWLEDGE_ONLY",
        "operational_data_access": "NONE",
        "message": (
            "The previous AI Assistant has been retired. "
            "A new knowledge-only Assistant is being developed."
        ),
    }


@router.post("/ask")
def ask_assistant() -> None:
    raise HTTPException(
        status_code=503,
        detail=(
            "AI Assistant is temporarily unavailable while the new "
            "knowledge-only Assistant is being developed."
        ),
    )

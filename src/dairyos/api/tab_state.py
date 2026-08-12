"""Authoritative operational read contract for the S-09D operator tabs.

S-09D.55 establishes one read surface for domain tabs. The endpoint exposes
current FarmOperationalState only; tab UIs must not infer current state by
replaying or aggregating the raw event journal.
"""

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container


router = APIRouter(
    prefix="/operations",
    tags=["Operational State"],
)

TAB_STATE_CONTRACT_VERSION = "S-09D.55"

TAB_DEFINITIONS: dict[str, dict[str, Any]] = {
    "animals": {"state_keys": ["animals"]},
    "milk": {"state_keys": ["milk_status", "milk_production_summary"]},
    "feed": {"state_keys": ["feeding_status"]},
    "health": {"state_keys": ["health_state", "health_alerts"]},
    "breeding": {"state_keys": ["breeding_status"]},
    "workforce": {"state_keys": ["workforce_status"]},
    "inventory": {"state_keys": ["inventory_status"]},
    "equipment": {"state_keys": ["equipment_status"]},
    "finance": {"state_keys": ["financial_status"]},
    "analytics": {
        "state_keys": [
            "milk_production_summary",
            "open_tasks",
            "completed_tasks",
            "operational_freshness",
        ]
    },
    "alerts": {
        "state_keys": ["exceptions", "heads_up_notifications", "unhandled_events"]
    },
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _tab_payload(state: Any, tab_id: str) -> dict[str, Any]:
    definition = TAB_DEFINITIONS[tab_id]
    values: dict[str, Any] = {}
    populated = False

    for key in definition["state_keys"]:
        value = getattr(state, key, None)
        safe_value = _json_safe(value)
        values[key] = safe_value
        if isinstance(safe_value, dict):
            populated = populated or bool(safe_value)
        elif isinstance(safe_value, list):
            populated = populated or bool(safe_value)
        elif safe_value not in (None, "", 0, False):
            populated = True

    attention = bool(
        tab_id == "alerts"
        and (
            getattr(state, "exceptions", None)
            or getattr(state, "heads_up_notifications", None)
        )
    )

    return {
        "tab_id": tab_id,
        "contract_version": TAB_STATE_CONTRACT_VERSION,
        "source": "FarmOperationalState",
        "farm_id": str(state.farm_id),
        "operational_date": str(state.operational_date),
        "status": "ATTENTION" if attention else ("ACTIVE" if populated else "NO_DATA"),
        "state": values,
    }


@router.get("/tab-state")
def get_tab_state(container=Depends(get_container)):
    """Return the complete authoritative read contract for all operator tabs."""

    state = container.farm_operational_state_service.get_state()
    return {
        "system": "DairyOS",
        "contract_version": TAB_STATE_CONTRACT_VERSION,
        "source": "FarmOperationalState",
        "farm_id": str(state.farm_id),
        "operational_date": str(state.operational_date),
        "tabs": {
            tab_id: _tab_payload(state, tab_id)
            for tab_id in TAB_DEFINITIONS
        },
    }


@router.get("/tab-state/{tab_id}")
def get_one_tab_state(tab_id: str, container=Depends(get_container)):
    """Return one tab's authoritative current-state payload."""

    if tab_id not in TAB_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Unknown operational tab: {tab_id}")

    state = container.farm_operational_state_service.get_state()
    return _tab_payload(state, tab_id)

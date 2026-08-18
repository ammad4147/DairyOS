"""Authoritative operational read contract for the S-09D operator tabs.

FarmOperationalState remains the authoritative operational-state projection.

The Animals tab is intentionally different: animal identity, lifecycle status,
and current milking eligibility belong to the canonical persisted Animal
Register. The tab therefore reads that register directly rather than relying
on the legacy ``FarmOperationalState.animals`` compatibility field, which is
not persisted as part of the operational-state JSON projection.
"""

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container


router = APIRouter(
    prefix="/operations",
    tags=["Operational State"],
)

TAB_STATE_CONTRACT_VERSION = "S-09D.56"

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
        "state_keys": [
            "exceptions",
            "heads_up_notifications",
            "unhandled_events",
        ]
    },
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _json_safe(item)
            for item in value
        ]

    return value


def _authoritative_animals_state(
    container,
) -> dict[str, dict[str, Any]]:
    """Build the Animals-tab projection from the canonical Animal Register."""

    animals = container.animal_repository.get_all()
    result: dict[str, dict[str, Any]] = {}

    for animal in animals or []:
        animal_id = getattr(
            animal,
            "animal_id",
            None,
        )

        if not animal_id:
            continue

        is_milking = bool(
            getattr(
                animal,
                "is_currently_milking",
                False,
            )
        )

        lifecycle_status = getattr(
            animal,
            "lifecycle_status",
            None,
        )

        result[str(animal_id)] = {
            "animal_id": str(animal_id),
            "animal_type": getattr(
                animal,
                "animal_type",
                None,
            ),
            "breed": getattr(
                animal,
                "breed",
                None,
            ),
            "sex": getattr(
                animal,
                "sex",
                None,
            ),
            "lifecycle_status": lifecycle_status,
            "status": (
                "MILKING"
                if is_milking
                else lifecycle_status
            ),
            "is_currently_milking": is_milking,
            "milking_frequency": getattr(
                animal,
                "milking_frequency",
                None,
            ),
            "production_group": getattr(
                animal,
                "production_group",
                None,
            ),
            "location": getattr(
                animal,
                "location",
                None,
            ),
            "active": bool(
                getattr(
                    animal,
                    "active",
                    True,
                )
            ),
            "non_milking_directive": getattr(
                animal,
                "non_milking_directive",
                "NONE",
            ),
            "non_milking_reason": getattr(
                animal,
                "non_milking_reason",
                None,
            ),
            "non_milking_since": getattr(
                animal,
                "non_milking_since",
                None,
            ),
            "non_milking_until": getattr(
                animal,
                "non_milking_until",
                None,
            ),
        }

    return _json_safe(result)


def _tab_payload(
    state: Any,
    tab_id: str,
    *,
    container: Any,
) -> dict[str, Any]:
    definition = TAB_DEFINITIONS[tab_id]
    values: dict[str, Any] = {}
    populated = False

    for key in definition["state_keys"]:
        if tab_id == "animals" and key == "animals":
            safe_value = _authoritative_animals_state(container)
        else:
            value = getattr(
                state,
                key,
                None,
            )
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
            or getattr(
                state,
                "heads_up_notifications",
                None,
            )
        )
    )

    return {
        "tab_id": tab_id,
        "contract_version": TAB_STATE_CONTRACT_VERSION,
        "source": "FarmOperationalState",
        "source_detail": (
            "Canonical Animal Register"
            if tab_id == "animals"
            else "FarmOperationalState"
        ),
        "farm_id": str(state.farm_id),
        "operational_date": str(state.operational_date),
        "status": (
            "ATTENTION"
            if attention
            else (
                "ACTIVE"
                if populated
                else "NO_DATA"
            )
        ),
        "state": values,
    }


@router.get("/tab-state")
def get_tab_state(
    container=Depends(get_container),
):
    """Return the complete authoritative read contract for all operator tabs."""

    state = container.farm_operational_state_service.get_state()

    return {
        "system": "DairyOS",
        "contract_version": TAB_STATE_CONTRACT_VERSION,
        "source": "FarmOperationalState",
        "farm_id": str(state.farm_id),
        "operational_date": str(state.operational_date),
        "tabs": {
            tab_id: _tab_payload(
                state,
                tab_id,
                container=container,
            )
            for tab_id in TAB_DEFINITIONS
        },
    }


@router.get("/tab-state/{tab_id}")
def get_one_tab_state(
    tab_id: str,
    container=Depends(get_container),
):
    """Return one tab's authoritative current-state payload."""

    if tab_id not in TAB_DEFINITIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown operational tab: {tab_id}",
        )

    state = container.farm_operational_state_service.get_state()

    return _tab_payload(
        state,
        tab_id,
        container=container,
    )

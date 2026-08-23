from __future__ import annotations

from collections.abc import Iterable

PERMISSIONS = (
    "dashboard.view",
    "animals.view", "animals.create", "animals.edit", "animals.disposition",
    "milk.view", "milk.create", "milk.edit",
    "feed.view", "feed.create", "feed.edit",
    "finance.view", "finance.create_feed", "finance.create_opex", "finance.edit", "finance.void",
    "breeding.view", "breeding.create", "breeding.edit",
    "health.view", "health.create", "health.edit",
    "coml.view", "analytics.view", "audit.view",
    "settings.view", "settings.farm_profile", "settings.standards",
    "users.view", "users.create", "users.edit", "users.disable",
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "OWNER": frozenset(PERMISSIONS),
    "MANAGER": frozenset({
        "dashboard.view",
        "animals.view", "animals.create", "animals.edit", "animals.disposition",
        "milk.view", "milk.create", "milk.edit",
        "feed.view", "feed.create", "feed.edit",
        "finance.view", "finance.create_feed", "finance.create_opex", "finance.edit",
        "breeding.view", "breeding.create", "breeding.edit",
        "health.view", "health.create", "health.edit",
        "coml.view", "analytics.view", "audit.view",
        "settings.view", "settings.farm_profile",
    }),
    "MILKER": frozenset({
        "dashboard.view",
        "animals.view",
        "milk.view", "milk.create",
        "feed.view", "feed.create",
        "health.view",
        "breeding.view",
    }),
}

ROLE_DESCRIPTIONS = {
    "OWNER": "Full farm, financial, administrative, and security control.",
    "MANAGER": "Operational management with financial entry/edit access; cannot manage users or void finance entries.",
    "MILKER": "Milk and feed operational entry with read-only animal, health, and breeding visibility.",
}


def permissions_for_role(role: str) -> frozenset[str]:
    normalized = str(role or "").strip().upper()
    if normalized not in ROLE_PERMISSIONS:
        return frozenset()
    return ROLE_PERMISSIONS[normalized]


def has_permission(role: str, permission: str) -> bool:
    return permission in permissions_for_role(role)


def normalize_permissions(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value in PERMISSIONS})

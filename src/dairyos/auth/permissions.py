from __future__ import annotations

from collections.abc import Iterable
import json

PERMISSIONS = (
    "dashboard.view",
    "dashboard.view_finance",
    "dashboard.view_profitability",
    "animals.view", "animals.create", "animals.edit", "animals.disposition",
    "milk.view", "milk.create", "milk.edit",
    "feed.view", "feed.create", "feed.edit",
    "finance.view", "finance.create_feed", "finance.create_opex", "finance.edit", "finance.void",
    "finance.view_profitability", "finance.view_cash",
    "breeding.view", "breeding.create", "breeding.edit",
    "health.view", "health.create", "health.edit",
    "coml.view", "analytics.view", "analytics.view_financial", "audit.view",
    "settings.view", "settings.farm_profile", "settings.standards", "settings.email",
    "users.view", "users.create", "users.edit", "users.disable", "users.permissions",
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "OWNER": frozenset(PERMISSIONS),
    "MANAGER": frozenset({
        "dashboard.view", "dashboard.view_finance", "dashboard.view_profitability",
        "animals.view", "animals.create", "animals.edit", "animals.disposition",
        "milk.view", "milk.create", "milk.edit",
        "feed.view", "feed.create", "feed.edit",
        "finance.view", "finance.create_feed", "finance.create_opex", "finance.edit",
        "finance.view_profitability", "finance.view_cash",
        "breeding.view", "breeding.create", "breeding.edit",
        "health.view", "health.create", "health.edit",
        "coml.view", "analytics.view", "analytics.view_financial", "audit.view",
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
    "CUSTOM": frozenset(),
}

ROLE_DESCRIPTIONS = {
    "OWNER": "Full farm, financial, administrative, and security preset.",
    "MANAGER": "Operational management preset; permissions can be customized per user.",
    "MILKER": "Milk/feed operational preset; permissions can be customized per user.",
    "CUSTOM": "No preset permissions. The administrator defines this user's access explicitly.",
}

PERMISSION_GROUPS: dict[str, tuple[str, ...]] = {
    "Dashboard": ("dashboard.view", "dashboard.view_finance", "dashboard.view_profitability"),
    "Animals": ("animals.view", "animals.create", "animals.edit", "animals.disposition"),
    "Milk": ("milk.view", "milk.create", "milk.edit"),
    "Feed": ("feed.view", "feed.create", "feed.edit"),
    "Finance": ("finance.view", "finance.create_feed", "finance.create_opex", "finance.edit", "finance.void", "finance.view_profitability", "finance.view_cash"),
    "Breeding": ("breeding.view", "breeding.create", "breeding.edit"),
    "Health": ("health.view", "health.create", "health.edit"),
    "COML": ("coml.view",),
    "Analytics": ("analytics.view", "analytics.view_financial"),
    "Audit": ("audit.view",),
    "Settings": ("settings.view", "settings.farm_profile", "settings.standards", "settings.email"),
    "User administration": ("users.view", "users.create", "users.edit", "users.disable", "users.permissions"),
}


def permissions_for_role(role: str) -> frozenset[str]:
    normalized = str(role or "").strip().upper()
    return ROLE_PERMISSIONS.get(normalized, frozenset())


def has_permission(role: str, permission: str) -> bool:
    return permission in permissions_for_role(role)


def normalize_permissions(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value in PERMISSIONS})


def default_permissions_json(role: str) -> str:
    return json.dumps(sorted(permissions_for_role(role)), separators=(",", ":"))


def permissions_from_json(value: str | None, role: str) -> frozenset[str]:
    if value is None or value == "":
        return permissions_for_role(role)
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError):
        return permissions_for_role(role)
    if not isinstance(decoded, list):
        return permissions_for_role(role)
    return frozenset(normalize_permissions(decoded))

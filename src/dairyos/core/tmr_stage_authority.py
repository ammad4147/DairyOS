"""Governed animal-to-TMR stage authority.

Animal.production_group is an operator-maintained biological feeding-stage
fact. Values are canonical and category-specific; unknown free text must never
be consumed by Feed Storage or COP calculations.
"""

from __future__ import annotations

CATEGORY_STAGE_MAP = {
    "Milking": ("early_milking", "mid_milking", "late_milking"),
    "Dry": ("far_off", "close_up"),
    "Heifer": ("heifer_growth",),
    "Female Calf": ("calf_starter",),
    "Male Calf": ("calf_starter",),
    "Bull": ("bull",),
}

STAGE_LABELS = {
    "early_milking": "Early Lactation",
    "mid_milking": "Mid Lactation",
    "late_milking": "Late Lactation",
    "far_off": "Far-Off Dry",
    "close_up": "Close-Up Dry",
    "heifer_growth": "Growing Heifer",
    "calf_starter": "Calf Starter",
    "bull": "Bull",
}

_STAGE_ALIASES = {
    "early_lactation": "early_milking",
    "mid_lactation": "mid_milking",
    "late_lactation": "late_milking",
    "far_off_dry": "far_off",
    "close_up_dry": "close_up",
    "growing_heifer": "heifer_growth",
}


def normalize_stage(value: object) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    normalized = text.replace("-", "_").replace(" ", "_")
    if normalized in STAGE_LABELS:
        return normalized
    return _STAGE_ALIASES.get(normalized)


def allowed_stages_for_category(category: str | None) -> tuple[str, ...]:
    return CATEGORY_STAGE_MAP.get(str(category or "").strip(), ())


def validate_stage_for_category(
    category: str | None,
    value: object,
    *,
    allow_blank: bool = True,
) -> str | None:
    stage = normalize_stage(value)
    if stage is None:
        if allow_blank and not str(value or "").strip():
            return None
        raise ValueError("Unknown TMR production group.")

    allowed = allowed_stages_for_category(category)
    if stage not in allowed:
        labels = ", ".join(STAGE_LABELS[item] for item in allowed) or "none"
        raise ValueError(
            f"Production Group '{value}' is not valid for {category or 'this category'}. "
            f"Allowed: {labels}."
        )
    return stage

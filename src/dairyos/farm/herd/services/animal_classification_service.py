"""Canonical animal classification and lifecycle translation rules.

This service is the single authority for translating persisted animal
sex/lifecycle facts into the operator-facing animal category and for
normalising legacy combinations that previously allowed a male animal to be
stored as ``HEIFER``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AnimalCategory(StrEnum):
    MILKING_COWS = "Milking Cows"
    DRY_COWS = "Dry Cows"
    HEIFERS = "Heifers"
    BULLS = "Bulls"
    FEMALE_CALVES = "Female Calves"
    MALE_CALVES = "Male Calves"
    EXITED = "Exited Animals"


class AnimalClassificationError(ValueError):
    """Raised when sex/lifecycle facts cannot form a valid classification."""


@dataclass(frozen=True)
class AnimalClassification:
    """Canonical representation consumed by API/UI adapters."""

    category: AnimalCategory
    lifecycle_status: str
    sex: str


class AnimalClassificationService:
    """Central authority for animal category/lifecycle translation."""

    LIFECYCLE_STATUSES = {
        "CALF",
        "HEIFER",
        "CLOSE_UP",
        "LACTATING",
        "DRY",
        "BULL",
        "SOLD",
        "CULLED",
        "DECEASED",
    }
    SEXES = {"FEMALE", "MALE"}

    @classmethod
    def normalise_lifecycle(cls, lifecycle_status: str | None, sex: str | None) -> str:
        lifecycle = str(lifecycle_status or "HEIFER").upper().strip()
        gender = str(sex or "FEMALE").upper().strip()

        if gender not in cls.SEXES:
            raise AnimalClassificationError(
                f"Invalid animal sex: {gender}. Allowed: FEMALE, MALE."
            )

        # Historical DairyOS records used HEIFER for male animals. That is
        # semantically incorrect; normalise the legacy pair to BULL.
        if gender == "MALE" and lifecycle == "HEIFER":
            lifecycle = "BULL"

        if lifecycle not in cls.LIFECYCLE_STATUSES:
            raise AnimalClassificationError(
                f"Invalid lifecycle status: {lifecycle}. "
                f"Allowed: {', '.join(sorted(cls.LIFECYCLE_STATUSES))}."
            )

        if gender == "MALE" and lifecycle in {"LACTATING", "DRY", "CLOSE_UP"}:
            raise AnimalClassificationError(
                f"Male animals cannot have lifecycle status {lifecycle}."
            )

        if gender == "FEMALE" and lifecycle == "BULL":
            raise AnimalClassificationError("Female animals cannot have BULL lifecycle status.")

        return lifecycle

    @classmethod
    def classify(
        cls,
        lifecycle_status: str | None,
        sex: str | None,
    ) -> AnimalClassification:
        gender = str(sex or "FEMALE").upper().strip()
        lifecycle = cls.normalise_lifecycle(lifecycle_status, gender)

        if lifecycle in {"SOLD", "CULLED", "DECEASED"}:
            category = AnimalCategory.EXITED
        elif lifecycle == "BULL":
            category = AnimalCategory.BULLS
        elif lifecycle == "LACTATING":
            category = AnimalCategory.MILKING_COWS
        elif lifecycle == "DRY":
            category = AnimalCategory.DRY_COWS
        elif lifecycle in {"HEIFER", "CLOSE_UP"}:
            category = AnimalCategory.HEIFERS
        elif lifecycle == "CALF" and gender == "MALE":
            category = AnimalCategory.MALE_CALVES
        else:
            category = AnimalCategory.FEMALE_CALVES

        return AnimalClassification(
            category=category,
            lifecycle_status=lifecycle,
            sex=gender,
        )

    @classmethod
    def from_category(
        cls,
        category: str,
        *,
        current_lifecycle: str | None = None,
    ) -> AnimalClassification:
        """Translate an operator-facing category into canonical facts."""
        candidate = str(category or "").strip()
        lookup = {
            AnimalCategory.MILKING_COWS.value: ("LACTATING", "FEMALE"),
            AnimalCategory.DRY_COWS.value: ("DRY", "FEMALE"),
            AnimalCategory.HEIFERS.value: ("HEIFER", "FEMALE"),
            AnimalCategory.BULLS.value: ("BULL", "MALE"),
            AnimalCategory.FEMALE_CALVES.value: ("CALF", "FEMALE"),
            AnimalCategory.MALE_CALVES.value: ("CALF", "MALE"),
        }

        if candidate == AnimalCategory.EXITED.value:
            lifecycle = cls.normalise_lifecycle(current_lifecycle or "SOLD", "FEMALE")
            return cls.classify(lifecycle, "FEMALE")

        try:
            lifecycle, sex = lookup[candidate]
        except KeyError as exc:
            raise AnimalClassificationError(
                f"Unknown animal category: {candidate}. "
                f"Allowed: {', '.join(sorted(item.value for item in AnimalCategory if item is not AnimalCategory.EXITED))}."
            ) from exc

        return cls.classify(lifecycle, sex)

    @classmethod
    def serialise(cls, lifecycle_status: str | None, sex: str | None) -> dict[str, str]:
        """Return canonical facts for JSON/API boundaries."""
        result = cls.classify(lifecycle_status, sex)
        return {
            "category": result.category.value,
            "lifecycle_status": result.lifecycle_status,
            "sex": result.sex,
        }


DEFAULT_ANIMAL_CLASSIFICATION_SERVICE = AnimalClassificationService()

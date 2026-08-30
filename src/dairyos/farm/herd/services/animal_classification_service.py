"""Canonical animal classification and lifecycle translation rules.

The persisted individual-animal category is singular. Aggregate population
labels are a presentation concern and must be pluralised by the consuming
herd/dashboard/report view rather than by the domain category itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AnimalCategory(StrEnum):
    """Canonical category for one individual animal."""

    MILKING = "Milking"
    DRY = "Dry"
    HEIFER = "Heifer"
    BULL = "Bull"
    FEMALE_CALF = "Female Calf"
    MALE_CALF = "Male Calf"
    EXITED = "Exited"


class AnimalClassificationError(ValueError):
    """Raised when sex/lifecycle facts cannot form a valid classification."""


@dataclass(frozen=True)
class AnimalClassification:
    """Canonical representation consumed by API/UI adapters."""

    category: AnimalCategory
    lifecycle_status: str
    sex: str


class AnimalClassificationService:
    """Central authority for individual-animal category/lifecycle translation."""

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
            category = AnimalCategory.BULL
        elif lifecycle == "LACTATING":
            category = AnimalCategory.MILKING
        elif lifecycle == "DRY":
            category = AnimalCategory.DRY
        elif lifecycle in {"HEIFER", "CLOSE_UP"}:
            category = AnimalCategory.HEIFER
        elif lifecycle == "CALF" and gender == "MALE":
            category = AnimalCategory.MALE_CALF
        else:
            category = AnimalCategory.FEMALE_CALF

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
        """Translate an individual-animal category into canonical facts."""
        candidate = str(category or "").strip()
        lookup = {
            AnimalCategory.MILKING.value: ("LACTATING", "FEMALE"),
            AnimalCategory.DRY.value: ("DRY", "FEMALE"),
            AnimalCategory.HEIFER.value: ("HEIFER", "FEMALE"),
            AnimalCategory.BULL.value: ("BULL", "MALE"),
            AnimalCategory.FEMALE_CALF.value: ("CALF", "FEMALE"),
            AnimalCategory.MALE_CALF.value: ("CALF", "MALE"),
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
        """Return canonical individual-animal facts for JSON/API boundaries."""
        result = cls.classify(lifecycle_status, sex)
        return {
            "category": result.category.value,
            "lifecycle_status": result.lifecycle_status,
            "sex": result.sex,
        }


DEFAULT_ANIMAL_CLASSIFICATION_SERVICE = AnimalClassificationService()

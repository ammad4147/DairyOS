"""Canonical animal classification and lifecycle translation rules.

The persisted individual-animal category is singular. Aggregate population
labels are presentation concerns and are translated at herd/dashboard/report
boundaries rather than becoming persisted individual categories.

Explicit operator-supplied biological facts are validated against canonical
classification rules. Canonicalization must never silently overwrite an
explicit contradictory fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AnimalCategory(StrEnum):
    """Canonical category for one individual animal.

    The singular members are canonical. The plural member names are retained
    as compatibility aliases because existing tests and application adapters
    historically referenced them, but their values remain singular.
    """

    MILKING = "Milking"
    DRY = "Dry"
    HEIFER = "Heifer"
    BULL = "Bull"
    FEMALE_CALF = "Female Calf"
    MALE_CALF = "Male Calf"
    EXITED = "Exited"

    # Backward-compatible enum-member aliases.
    MILKING_COWS = "Milking"
    DRY_COWS = "Dry"
    HEIFERS = "Heifer"
    BULLS = "Bull"
    FEMALE_CALVES = "Female Calf"
    MALE_CALVES = "Male Calf"


class AnimalClassificationError(ValueError):
    """Raised when supplied animal facts cannot form a valid classification."""


@dataclass(frozen=True)
class AnimalClassification:
    """Canonical representation consumed by API/UI adapters."""

    category: AnimalCategory
    lifecycle_status: str
    sex: str


class AnimalClassificationService:
    """Central authority for individual-animal classification rules."""

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
    def normalise_sex(cls, sex: str | None) -> str:
        """Return a canonical sex value or reject an invalid value."""

        gender = str(sex or "FEMALE").upper().strip()

        if gender not in cls.SEXES:
            raise AnimalClassificationError(
                f"Invalid animal sex: {gender}. Allowed: FEMALE, MALE."
            )

        return gender

    @classmethod
    def normalise_lifecycle(
        cls,
        lifecycle_status: str | None,
        sex: str | None,
    ) -> str:
        """Return a canonical lifecycle status or reject an invalid value."""

        lifecycle = str(lifecycle_status or "HEIFER").upper().strip()
        gender = cls.normalise_sex(sex)

        # Historical DairyOS records used HEIFER for male animals. That is
        # semantically incorrect; normalise the legacy pair to BULL.
        if gender == "MALE" and lifecycle == "HEIFER":
            lifecycle = "BULL"

        if lifecycle not in cls.LIFECYCLE_STATUSES:
            raise AnimalClassificationError(
                f"Invalid lifecycle status: {lifecycle}. "
                f"Allowed: {', '.join(sorted(cls.LIFECYCLE_STATUSES))}."
            )

        if gender == "MALE" and lifecycle in {
            "LACTATING",
            "DRY",
            "CLOSE_UP",
        }:
            raise AnimalClassificationError(
                f"Male animals cannot have lifecycle status {lifecycle}."
            )

        if gender == "FEMALE" and lifecycle == "BULL":
            raise AnimalClassificationError(
                "Female animals cannot have BULL lifecycle status."
            )

        return lifecycle

    @classmethod
    def classify(
        cls,
        lifecycle_status: str | None,
        sex: str | None,
    ) -> AnimalClassification:
        """Classify one individual animal from its biological state."""

        gender = cls.normalise_sex(sex)
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
        explicit_sex: str | None = None,
    ) -> AnimalClassification:
        """Translate a category into canonical biological facts.

        If the operator explicitly supplies sex, it is treated as a fact that
        must agree with the category. A contradictory explicit value is a
        validation error; it is never silently canonicalized.
        """

        candidate = str(category or "").strip()

        lookup = {
            AnimalCategory.MILKING.value: ("LACTATING", "FEMALE"),
            AnimalCategory.DRY.value: ("DRY", "FEMALE"),
            AnimalCategory.HEIFER.value: ("HEIFER", "FEMALE"),
            AnimalCategory.BULL.value: ("BULL", "MALE"),
            AnimalCategory.FEMALE_CALF.value: ("CALF", "FEMALE"),
            AnimalCategory.MALE_CALF.value: ("CALF", "MALE"),

            # Aggregate labels are compatibility inputs only.
            "Milking Cows": ("LACTATING", "FEMALE"),
            "Dry Cows": ("DRY", "FEMALE"),
            "Heifers": ("HEIFER", "FEMALE"),
            "Bulls": ("BULL", "MALE"),
            "Female Calves": ("CALF", "FEMALE"),
            "Male Calves": ("CALF", "MALE"),
        }

        if candidate == AnimalCategory.EXITED.value:
            lifecycle = cls.normalise_lifecycle(
                current_lifecycle or "SOLD",
                "FEMALE",
            )
            classification = cls.classify(lifecycle, "FEMALE")

            if explicit_sex is not None:
                supplied_sex = cls.normalise_sex(explicit_sex)

                if supplied_sex != classification.sex:
                    raise AnimalClassificationError(
                        "Explicit animal sex conflicts with the canonical "
                        f"category '{candidate}': expected "
                        f"{classification.sex}, received {supplied_sex}."
                    )

            return classification

        try:
            lifecycle, canonical_sex = lookup[candidate]
        except KeyError as exc:
            allowed = (
                "Milking, Dry, Heifer, Female Calf, Male Calf, Bull"
            )
            raise AnimalClassificationError(
                f"Unknown animal category: {candidate}. Allowed: {allowed}."
            ) from exc

        if explicit_sex is not None:
            supplied_sex = cls.normalise_sex(explicit_sex)

            if supplied_sex != canonical_sex:
                raise AnimalClassificationError(
                    "Explicit animal sex conflicts with the canonical "
                    f"category '{candidate}': expected "
                    f"{canonical_sex}, received {supplied_sex}."
                )

        return cls.classify(lifecycle, canonical_sex)

    @classmethod
    def serialise(
        cls,
        lifecycle_status: str | None,
        sex: str | None,
    ) -> dict[str, str]:
        """Return canonical individual-animal facts for JSON/API boundaries."""

        result = cls.classify(lifecycle_status, sex)

        return {
            "category": result.category.value,
            "lifecycle_status": result.lifecycle_status,
            "sex": result.sex,
        }


DEFAULT_ANIMAL_CLASSIFICATION_SERVICE = AnimalClassificationService()

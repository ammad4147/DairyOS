"""Validation for persisted animal parentage links.

Parentage is part of the animal master record, not free-form profile text.
This service keeps the API and registration paths on the same biological
integrity boundary while leaving historical records available for review.
"""

from __future__ import annotations

from datetime import date


class AnimalParentageError(ValueError):
    """Raised when a dam/sire link cannot be a valid biological fact."""


def _normalise_id(value):
    if value in (None, ""):
        return None
    value = str(value).strip()
    return value or None


def _would_create_cycle(repository, child_id: str, parent_id: str) -> bool:
    """Return whether assigning ``parent_id`` would make an ancestry cycle."""

    pending = [parent_id]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        if current == child_id:
            return True
        parent = repository.get_by_animal_id(current)
        if parent is None:
            continue
        for ancestor_id in (
            getattr(parent, "dam_id", None),
            getattr(parent, "sire_id", None),
        ):
            ancestor_id = _normalise_id(ancestor_id)
            if ancestor_id:
                pending.append(ancestor_id)
    return False


def validate_parentage(
    repository,
    *,
    child_id: str,
    dam_id=None,
    sire_id=None,
    child_date_of_birth: date | None = None,
) -> tuple[str | None, str | None]:
    """Validate and canonicalise parent IDs for one animal.

    Parents must exist, have the expected sex, precede the child when dates
    are known, and may not introduce a self-reference or ancestry cycle.
    """

    child_id = _normalise_id(child_id)
    dam_id = _normalise_id(dam_id)
    sire_id = _normalise_id(sire_id)
    if not child_id:
        raise AnimalParentageError("child animal_id is required")
    if dam_id and sire_id and dam_id == sire_id:
        raise AnimalParentageError("dam_id and sire_id must identify different animals")

    for field, parent_id, expected_sex in (
        ("dam_id", dam_id, "FEMALE"),
        ("sire_id", sire_id, "MALE"),
    ):
        if not parent_id:
            continue
        if parent_id == child_id:
            raise AnimalParentageError(f"{field} cannot reference the animal itself")
        parent = repository.get_by_animal_id(parent_id)
        if parent is None:
            raise AnimalParentageError(f"{field} '{parent_id}' does not exist")
        actual_sex = str(getattr(parent, "sex", "") or "").strip().upper()
        if actual_sex != expected_sex:
            raise AnimalParentageError(
                f"{field} '{parent_id}' must reference a {expected_sex.lower()} animal"
            )
        parent_birth = getattr(parent, "date_of_birth", None)
        if (
            child_date_of_birth is not None
            and isinstance(parent_birth, date)
            and parent_birth >= child_date_of_birth
        ):
            raise AnimalParentageError(
                f"{field} '{parent_id}' must be older than the child"
            )
        if _would_create_cycle(repository, child_id, parent_id):
            raise AnimalParentageError(
                f"{field} '{parent_id}' would create an ancestry cycle"
            )

    return dam_id, sire_id

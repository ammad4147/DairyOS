from __future__ import annotations

from datetime import datetime, timezone

from dairyos.farm.production.models.non_milking_directive import (
    NonMilkingDirective,
)


class NonMilkingDirectiveService:
    """Authoritative animal-level veterinary milking directive service.

    Veterinary treatment may impose a temporary non-milking instruction,
    require milk to be separated from the normal farm milk stream, or make
    an animal permanently non-milking.

    This service owns animal participation state. It deliberately does not
    create milk disposition records.
    """

    FINDING_DEDUPE_PREFIX = "NON_MILKING_DIRECTIVE"

    def __init__(
        self,
        animal_repository,
        finding_service=None,
    ):
        self.animal_repository = animal_repository
        self.finding_service = finding_service

    def apply(
        self,
        animal_id: str,
        directive: NonMilkingDirective,
        *,
        reason: str | None = None,
        changed_by: str | None = None,
        effective_until: datetime | None = None,
    ):
        directive = NonMilkingDirective(directive)

        if directive is NonMilkingDirective.NONE:
            return self.clear(
                animal_id,
                changed_by=changed_by,
                reason=reason,
            )

        animal = self._get_animal(animal_id)

        # Preserve whether this animal was actually part of the active
        # milking herd before the veterinary restriction was imposed.
        animal.non_milking_restore_to_milking = bool(
            getattr(animal, "is_currently_milking", False)
        )

        now = datetime.now(timezone.utc)

        animal.non_milking_directive = directive.value
        animal.non_milking_since = now
        animal.non_milking_until = effective_until
        animal.non_milking_reason = reason
        animal.non_milking_changed_by = changed_by

        # Every veterinary directive removes the animal from the active
        # milking-herd population.
        animal.is_currently_milking = False
        animal.lifecycle_status = "DRY"
        animal.updated_at = now

        saved = self._persist(animal)

        self._raise_finding(saved, directive, reason)

        return saved

    def clear(
        self,
        animal_id: str,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
    ):
        animal = self._get_animal(animal_id)

        restore_to_milking = bool(
            getattr(
                animal,
                "non_milking_restore_to_milking",
                False,
            )
        )

        previous_directive = self.get_directive(
            animal_id,
        )

        now = datetime.now(timezone.utc)

        animal.non_milking_directive = (
            NonMilkingDirective.NONE.value
        )
        animal.non_milking_since = None
        animal.non_milking_until = None
        animal.non_milking_reason = reason
        animal.non_milking_changed_by = changed_by
        animal.non_milking_restore_to_milking = False

        animal.is_currently_milking = restore_to_milking
        animal.lifecycle_status = (
            "LACTATING"
            if restore_to_milking
            else "DRY"
        )
        animal.updated_at = now

        saved = self._persist(animal)

        self._resolve_finding(
            saved,
            previous_directive,
            changed_by,
            reason,
        )

        return saved

    def get_directive(
        self,
        animal_id: str,
    ) -> NonMilkingDirective:
        animal = self._get_animal(animal_id)

        raw = getattr(
            animal,
            "non_milking_directive",
            NonMilkingDirective.NONE.value,
        )

        try:
            return NonMilkingDirective(str(raw))
        except ValueError:
            return NonMilkingDirective.NONE

    @staticmethod
    def is_outside_active_milking_herd(
        animal,
    ) -> bool:
        raw = getattr(
            animal,
            "non_milking_directive",
            NonMilkingDirective.NONE.value,
        )

        try:
            directive = NonMilkingDirective(str(raw))
        except ValueError:
            directive = NonMilkingDirective.NONE

        return directive.is_outside_active_milking_herd

    @staticmethod
    def expects_milk(animal) -> bool:
        raw = getattr(
            animal,
            "non_milking_directive",
            NonMilkingDirective.NONE.value,
        )

        try:
            directive = NonMilkingDirective(str(raw))
        except ValueError:
            directive = NonMilkingDirective.NONE

        return directive.expects_milk

    def _raise_finding(
        self,
        animal,
        directive: NonMilkingDirective,
        reason: str | None,
    ):
        if self.finding_service is None:
            return None

        return self.finding_service.raise_or_update(
            source_module="HEALTH",
            severity="HIGH",
            title=(
                f"Veterinary non-milking directive active for "
                f"{animal.animal_id}"
            ),
            detail=(
                f"Directive {directive.value} is active for "
                f"animal {animal.animal_id}. "
                f"The animal is outside the active milking herd. "
                f"Veterinary clearance is required before normal "
                f"milking participation is restored."
                + (
                    f" Reason: {reason}."
                    if reason
                    else ""
                )
            ),
            subject_type="ANIMAL",
            subject_id=str(animal.animal_id),
            route=(
                f"/farm/animals/{animal.animal_id}"
            ),
            dedupe_key=(
                f"{self.FINDING_DEDUPE_PREFIX}:"
                f"{animal.animal_id}"
            ),
        )

    def _resolve_finding(
        self,
        animal,
        previous_directive,
        changed_by,
        reason,
    ):
        if (
            self.finding_service is None
            or previous_directive is NonMilkingDirective.NONE
        ):
            return None

        repository = self.finding_service.repository

        finding = repository.find_open_by_dedupe_key(
            f"{self.FINDING_DEDUPE_PREFIX}:{animal.animal_id}"
        )

        if finding is None:
            return None

        note = (
            reason
            or "Veterinary clearance restored the animal's milking state."
        )

        return self.finding_service.resolve(
            finding.finding_id,
            operator=changed_by or "Veterinarian",
            resolution_note=note,
        )

    def _get_animal(self, animal_id: str):
        animal = self.animal_repository.get_by_animal_id(
            str(animal_id)
        )

        if animal is None:
            raise ValueError(
                f"Animal not found: {animal_id}"
            )

        return animal

    def _persist(self, animal):
        save = getattr(
            self.animal_repository,
            "save",
            None,
        )

        if callable(save):
            return save(animal)

        add = getattr(
            self.animal_repository,
            "add",
            None,
        )

        if callable(add):
            return add(animal)

        session = getattr(
            self.animal_repository,
            "session",
            None,
        )

        if session is not None:
            session.add(animal)
            session.commit()
            session.refresh(animal)

        return animal

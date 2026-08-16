from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)
from dairyos.farm.production.models.non_milking_directive import (
    NonMilkingDirective,
)
from dairyos.farm.production.services.non_milking_directive_service import (
    NonMilkingDirectiveService,
)


router = APIRouter(
    prefix="/farm",
    tags=["Veterinary Non-Milking"],
)


class VeterinaryNonMilkingDirectiveRequest(BaseModel):
    directive: NonMilkingDirective
    reason: str | None = None
    changed_by: str | None = None
    effective_until: datetime | None = None
    treatment_id: int | None = None


def _finding_service(factory):
    return OperationalFindingService(
        factory.operational_findings()
    )


def _resolve_directive_findings(factory, animal_id: str):
    repository = factory.operational_findings()

    for finding in repository.get_all():
        if finding.status == "RESOLVED":
            continue

        if (
            finding.subject_type == "ANIMAL"
            and finding.subject_id == str(animal_id)
            and finding.dedupe_key in {
                f"NON_MILKING_DIRECTIVE:{animal_id}",
                f"MILK_SEPARATELY:{animal_id}",
            }
        ):
            finding.status = "RESOLVED"
            finding.resolved_at = datetime.now(
                timezone.utc
            )
            finding.resolved_by = "Veterinary clearance"
            finding.resolution_note = (
                "Veterinary non-milking restriction cleared."
            )

    if repository.session:
        repository.session.commit()


@router.post(
    "/animals/{animal_id}/non-milking-directive"
)
def apply_veterinary_non_milking_directive(
    animal_id: str,
    payload: VeterinaryNonMilkingDirectiveRequest,
    container=Depends(get_container),
):
    factory = getattr(
        container,
        "repository_factory",
        None,
    )

    owns_factory = False

    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        animal = factory.animal().get_by_animal_id(
            str(animal_id)
        )

        if animal is None:
            raise HTTPException(
                status_code=404,
                detail=f"Animal not found: {animal_id}",
            )

        directive_service = NonMilkingDirectiveService(
            factory.animal()
        )

        if payload.directive is NonMilkingDirective.NONE:
            updated = directive_service.clear(
                str(animal_id),
                changed_by=payload.changed_by,
                reason=payload.reason,
            )

            _resolve_directive_findings(
                factory,
                str(animal_id),
            )

            return {
                "status": "CLEARED",
                "animal_id": updated.animal_id,
                "directive": updated.non_milking_directive,
                "lifecycle_status": updated.lifecycle_status,
                "is_currently_milking": (
                    updated.is_currently_milking
                ),
                "milk_expected": True,
                "message": (
                    "Veterinary non-milking restriction cleared. "
                    "Animal eligibility restored according to its "
                    "previous milking state."
                ),
            }

        updated = directive_service.apply(
            str(animal_id),
            payload.directive,
            reason=payload.reason,
            changed_by=payload.changed_by,
            effective_until=payload.effective_until,
        )

        findings = _finding_service(factory)

        if (
            payload.directive
            is NonMilkingDirective.MILK_SEPARATELY
        ):
            findings.raise_or_update(
                source_module="HEALTH",
                severity="HIGH",
                title=(
                    f"{animal_id}: milk must be separated"
                ),
                detail=(
                    "Veterinary instruction requires this animal "
                    "to remain outside the normal milking herd. "
                    "Milk is expected but must not enter normal "
                    "farm saleable milk."
                ),
                subject_type="ANIMAL",
                subject_id=str(animal_id),
                route=f"/farm/animals/{animal_id}",
                dedupe_key=f"MILK_SEPARATELY:{animal_id}",
            )

            findings.raise_or_update(
                source_module="HEALTH",
                severity="HIGH",
                title=(
                    f"Milk separation active: {animal_id}"
                ),
                detail=(
                    f"{animal_id} requires separate milk handling "
                    "under veterinary direction."
                ),
                subject_type="FARM",
                subject_id="FARM",
                route="/farm/command-center",
                dedupe_key=f"MILK_SEPARATELY:{animal_id}",
            )

        else:
            findings.raise_or_update(
                source_module="HEALTH",
                severity="HIGH",
                title=(
                    f"{animal_id}: non-milking directive active"
                ),
                detail=(
                    f"{animal_id} is outside the active milking herd "
                    f"under {payload.directive.value}. "
                    "Milk expectation is zero for this directive."
                ),
                subject_type="ANIMAL",
                subject_id=str(animal_id),
                route=f"/farm/animals/{animal_id}",
                dedupe_key=f"NON_MILKING_DIRECTIVE:{animal_id}",
            )

            findings.raise_or_update(
                source_module="HEALTH",
                severity="HIGH",
                title=(
                    f"Non-milking restriction active: {animal_id}"
                ),
                detail=(
                    f"{animal_id} is currently outside the active "
                    "milking herd under veterinary direction."
                ),
                subject_type="FARM",
                subject_id="FARM",
                route="/farm/command-center",
                dedupe_key=f"NON_MILKING_DIRECTIVE:{animal_id}",
            )

        return {
            "status": "APPLIED",
            "animal_id": updated.animal_id,
            "directive": updated.non_milking_directive,
            "non_milking_since": (
                updated.non_milking_since.isoformat()
                if updated.non_milking_since
                else None
            ),
            "non_milking_until": (
                updated.non_milking_until.isoformat()
                if updated.non_milking_until
                else None
            ),
            "non_milking_reason": (
                updated.non_milking_reason
            ),
            "non_milking_changed_by": (
                updated.non_milking_changed_by
            ),
            "lifecycle_status": updated.lifecycle_status,
            "is_currently_milking": (
                updated.is_currently_milking
            ),
            "milk_expected": (
                payload.directive.expects_milk
            ),
            "treatment_id": payload.treatment_id,
        }

    finally:
        if owns_factory:
            factory.close()

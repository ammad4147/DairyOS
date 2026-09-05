from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)


class MilkFindingService:
    """Milk finding adapter over the authoritative OperationalFinding lifecycle."""

    def __init__(self, repository):
        self.repository = repository
        self._service = OperationalFindingService(repository)

    def raise_or_update(
        self,
        *,
        severity: str,
        title: str,
        detail: str,
        subject_type: str,
        subject_id: str,
        route: str,
        dedupe_key: str,
    ):
        return self._service.raise_or_update(
            source_module="MILK",
            severity=severity,
            title=title,
            detail=detail,
            subject_type=subject_type,
            subject_id=subject_id,
            route=route,
            dedupe_key=dedupe_key,
        )

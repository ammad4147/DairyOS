from datetime import datetime

from dairyos.core.time_utils import utcnow
from dairyos.data.models.operational_finding import OperationalFinding


class MilkFindingService:
    """Write milk-derived findings through the existing OperationalFinding entity."""

    def __init__(self, repository):
        self.repository = repository

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
        now = utcnow()
        existing = self.repository.find_open_by_dedupe_key(dedupe_key)
        if existing is not None:
            existing.severity = severity
            existing.title = title
            existing.detail = detail
            existing.last_observed_at = now
            existing.observation_count = int(existing.observation_count or 0) + 1
            if self.repository.session:
                self.repository.session.commit()
                self.repository.session.refresh(existing)
            return existing

        prefix = f"AL-{now.strftime('%y%m%d')}"
        sequence = self.repository.count_opened_on(prefix) + 1
        finding = OperationalFinding(
            finding_id=f"{prefix}-{sequence:03d}",
            source_module="MILK",
            subject_type=subject_type,
            subject_id=subject_id,
            severity=severity,
            title=title,
            detail=detail,
            status="RAISED",
            route=route,
            dedupe_key=dedupe_key,
            observation_count=1,
            raised_at=now,
            last_observed_at=now,
        )
        return self.repository.add(finding)

from datetime import datetime, timezone

from dairyos.core.time_utils import utcnow
from dairyos.data.models.operational_finding import OperationalFinding

FINDING_PREFIXES = {
    "MILK": "AL",
    "HEALTH": "HL",
    "BREEDING": "BR",
    "INVENTORY": "INV",
    "EQUIPMENT": "EQ",
    "FEED": "FD",
    "WORKFORCE": "WF",
    "FINANCE": "FN",
}

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MONITORING", "INFORMATION"}


class OperationalFindingService:
    """Persistent lifecycle for operational findings and audit actions."""

    def __init__(self, repository):
        self.repository = repository

    def _allocate_finding_id(self, module: str) -> str:
        prefix = FINDING_PREFIXES[module]
        date_prefix = f"{prefix}-{datetime.now(timezone.utc).strftime('%y%m%d')}"
        sequence = self.repository.count_opened_on(date_prefix) + 1
        candidate = f"{date_prefix}-{sequence:03d}"
        while self.repository.get_by_finding_id(candidate) is not None:
            sequence += 1
            candidate = f"{date_prefix}-{sequence:03d}"
        return candidate

    def raise_or_update(
        self,
        *,
        source_module: str,
        severity: str,
        title: str,
        detail: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        route: str | None = None,
        dedupe_key: str | None = None,
    ) -> OperationalFinding:
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"Unknown finding severity: {severity}")
        if source_module not in FINDING_PREFIXES:
            raise ValueError(f"Unknown finding source_module: {source_module}")

        existing = self.repository.find_open_by_dedupe_key(dedupe_key) if dedupe_key else None
        if existing is not None:
            existing.severity = severity
            existing.title = title
            existing.detail = detail
            existing.observation_count = (existing.observation_count or 1) + 1
            existing.last_observed_at = utcnow()
            if self.repository.session:
                self.repository.session.commit()
                self.repository.session.refresh(existing)
            return existing

        finding = OperationalFinding(
            finding_id=self._allocate_finding_id(source_module),
            source_module=source_module,
            subject_type=subject_type,
            subject_id=subject_id,
            severity=severity,
            title=title,
            detail=detail,
            status="RAISED",
            route=route,
            dedupe_key=dedupe_key,
            observation_count=1,
        )
        return self.repository.add(finding)

    def acknowledge(self, finding_id: str, *, operator: str) -> OperationalFinding:
        finding = self.repository.get_by_finding_id(finding_id)
        if finding is None:
            raise KeyError(f"No finding with id {finding_id}")
        finding.status = "ACKNOWLEDGED"
        finding.acknowledged_at = utcnow()
        finding.acknowledged_by = operator
        if self.repository.session:
            self.repository.session.commit()
            self.repository.session.refresh(finding)
        return finding

    def resolve(self, finding_id: str, *, operator: str, resolution_note: str | None = None) -> OperationalFinding:
        finding = self.repository.get_by_finding_id(finding_id)
        if finding is None:
            raise KeyError(f"No finding with id {finding_id}")
        if finding.severity == "CRITICAL" and not (resolution_note or "").strip():
            raise ValueError("A resolution note is required to resolve a CRITICAL finding.")
        finding.status = "RESOLVED"
        finding.resolved_at = utcnow()
        finding.resolved_by = operator
        finding.resolution_note = resolution_note
        if self.repository.session:
            self.repository.session.commit()
            self.repository.session.refresh(finding)
        return finding

    def reinstate(self, finding_id: str, *, operator: str, reason: str) -> OperationalFinding:
        finding = self.repository.get_by_finding_id(finding_id)
        if finding is None:
            raise KeyError(f"No finding with id {finding_id}")
        if finding.status != "RESOLVED":
            raise ValueError("Only a RESOLVED finding can be reinstated.")
        if not (reason or "").strip():
            raise ValueError("A reinstatement reason is required.")
        finding.status = "REINSTATED"
        finding.reinstated_at = utcnow()
        finding.reinstated_by = operator
        finding.reinstate_reason = reason.strip()
        if self.repository.session:
            self.repository.session.commit()
            self.repository.session.refresh(finding)
        return finding

    def list(self, *, module: str | None = None, status: str | None = None, severity: str | None = None):
        findings = self.repository.get_all()
        if module is not None:
            findings = [f for f in findings if f.source_module == module]
        if status is not None:
            findings = [f for f in findings if f.status == status]
        if severity is not None:
            findings = [f for f in findings if f.severity == severity]
        return findings

    def counts_by_module(self) -> dict:
        return self.repository.count_open_by_module()

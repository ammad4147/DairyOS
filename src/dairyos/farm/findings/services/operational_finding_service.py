from datetime import datetime, timezone

from dairyos.core.time_utils import utcnow
from dairyos.data.models.operational_finding import OperationalFinding
from dairyos.data.models.operational_finding_lifecycle_event import (
    OperationalFindingLifecycleEvent,
)

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

    def _append_event(
        self,
        finding_id: str,
        event_type: str,
        *,
        operator: str | None = None,
        note: str | None = None,
        linked_event_id: int | None = None,
        occurred_at=None,
    ) -> OperationalFindingLifecycleEvent:
        event = OperationalFindingLifecycleEvent(
            finding_id=finding_id,
            event_type=event_type,
            occurred_at=occurred_at or utcnow(),
            operator=operator,
            note=(note.strip() if isinstance(note, str) else note),
            linked_event_id=linked_event_id,
        )
        return self.repository.add_lifecycle_event(event)

    def history(self, finding_id: str):
        return self.repository.get_lifecycle_events(finding_id)

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
            observed_at = utcnow()
            existing.severity = severity
            existing.title = title
            existing.detail = detail
            existing.observation_count = (existing.observation_count or 1) + 1
            existing.last_observed_at = observed_at
            if self.repository.session:
                self.repository.session.commit()
                self.repository.session.refresh(existing)
            self._append_event(
                existing.finding_id,
                "OBSERVED",
                note=detail,
                occurred_at=observed_at,
            )
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
        finding = self.repository.add(finding)
        self._append_event(
            finding.finding_id,
            "RAISED",
            note=detail,
            occurred_at=finding.raised_at,
        )
        return finding

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
        self._append_event(
            finding_id,
            "ACKNOWLEDGED",
            operator=operator,
            occurred_at=finding.acknowledged_at,
        )
        return finding

    def resolve(
        self,
        finding_id: str,
        *,
        operator: str,
        resolution_note: str | None = None,
    ) -> OperationalFinding:
        finding = self.repository.get_by_finding_id(finding_id)
        if finding is None:
            raise KeyError(f"No finding with id {finding_id}")

        note = (resolution_note or "").strip()
        if finding.severity == "CRITICAL" and not note:
            raise ValueError(
                "A resolution note is required to resolve a CRITICAL finding."
            )

        linked_reinstatement = None
        if finding.status == "REINSTATED":
            if not note:
                raise ValueError(
                    "A resolution note is required to resolve a reinstated finding."
                )
            linked_reinstatement = self.repository.latest_lifecycle_event(
                finding_id,
                "REINSTATED",
            )

        finding.status = "RESOLVED"
        finding.resolved_at = utcnow()
        finding.resolved_by = operator
        finding.resolution_note = resolution_note
        if self.repository.session:
            self.repository.session.commit()
            self.repository.session.refresh(finding)

        self._append_event(
            finding_id,
            "RESOLVED",
            operator=operator,
            note=resolution_note,
            linked_event_id=(
                linked_reinstatement.id
                if linked_reinstatement is not None
                else None
            ),
            occurred_at=finding.resolved_at,
        )
        return finding

    def reinstate(
        self,
        finding_id: str,
        *,
        operator: str,
        reason: str,
    ) -> OperationalFinding:
        finding = self.repository.get_by_finding_id(finding_id)
        if finding is None:
            raise KeyError(f"No finding with id {finding_id}")
        if finding.status != "RESOLVED":
            raise ValueError("Only a RESOLVED finding can be reinstated.")

        reason = (reason or "").strip()
        if not reason:
            raise ValueError("A reinstatement reason is required.")

        prior_resolution = self.repository.latest_lifecycle_event(
            finding_id,
            "RESOLVED",
        )

        finding.status = "REINSTATED"
        finding.reinstated_at = utcnow()
        finding.reinstated_by = operator
        finding.reinstate_reason = reason
        if self.repository.session:
            self.repository.session.commit()
            self.repository.session.refresh(finding)

        self._append_event(
            finding_id,
            "REINSTATED",
            operator=operator,
            note=reason,
            linked_event_id=(
                prior_resolution.id
                if prior_resolution is not None
                else None
            ),
            occurred_at=finding.reinstated_at,
        )
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

"""Operational Finding lifecycle endpoints (AA-013 §4, D-UI-5).

Findings are raised by detection engines; operators can acknowledge, resolve,
and administrators can persistently reinstate a resolved finding with a
reason.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.findings.services.operational_finding_service import OperationalFindingService

router = APIRouter(prefix="/farm/findings", tags=["Operational Findings"])


class AcknowledgeFindingRequest(BaseModel):
    operator: str = Field(default="UI Operator", min_length=1)


class ResolveFindingRequest(BaseModel):
    operator: str = Field(default="UI Operator", min_length=1)
    resolution_note: str | None = None


class ReinstateFindingRequest(BaseModel):
    operator: str = Field(default="UI Operator", min_length=1)
    reason: str = Field(min_length=1)


def _event_dict(event) -> dict[str, Any]:
    return {
        "event_id": event.id,
        "event_type": event.event_type,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        "operator": event.operator,
        "note": event.note,
        "linked_event_id": event.linked_event_id,
    }


def _finding_dict(
    finding,
    service: OperationalFindingService | None = None,
) -> dict[str, Any]:
    return {
        "finding_id": finding.finding_id,
        "source_module": finding.source_module,
        "subject_type": finding.subject_type,
        "subject_id": finding.subject_id,
        "severity": finding.severity,
        "title": finding.title,
        "detail": finding.detail,
        "status": finding.status,
        "route": finding.route,
        "observation_count": finding.observation_count,
        "raised_at": finding.raised_at.isoformat() if finding.raised_at else None,
        "last_observed_at": finding.last_observed_at.isoformat() if finding.last_observed_at else None,
        "acknowledged_at": finding.acknowledged_at.isoformat() if finding.acknowledged_at else None,
        "acknowledged_by": finding.acknowledged_by,
        "resolved_at": finding.resolved_at.isoformat() if finding.resolved_at else None,
        "resolved_by": finding.resolved_by,
        "resolution_note": finding.resolution_note,
        "reinstated_at": finding.reinstated_at.isoformat() if finding.reinstated_at else None,
        "reinstated_by": finding.reinstated_by,
        "reinstate_reason": finding.reinstate_reason,
        "lifecycle_events": [
            _event_dict(event)
            for event in (
                service.history(finding.finding_id)
                if service is not None
                else []
            )
        ],
    }


def _service() -> tuple[OperationalFindingService, RepositoryFactory]:
    rf = RepositoryFactory.create()
    return OperationalFindingService(rf.operational_findings()), rf


def _as_day(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _milk_row_total(row: Any) -> float | None:
    total = getattr(row, "total_yield", None)
    if total is not None:
        return float(total)

    values = [
        getattr(row, "morning_yield", None),
        getattr(row, "afternoon_yield", None),
        getattr(row, "evening_yield", None),
    ]
    entered = [float(value) for value in values if value is not None]
    return sum(entered) if entered else None


def _yield_drop_detail(finding: Any, rf: RepositoryFactory) -> dict[str, Any]:
    animal_id = str(finding.subject_id or "").strip()
    if finding.source_module != "MILK" or not animal_id:
        raise HTTPException(
            status_code=422,
            detail="Yield-drop detail is available only for animal-linked MILK findings.",
        )

    as_of = _as_day(finding.last_observed_at or finding.raised_at)
    daily: dict[date, float] = defaultdict(float)

    for row in rf.milk().get_all():
        if str(getattr(row, "animal_id", "")) != animal_id:
            continue
        if not bool(getattr(row, "session_ledger", False)):
            continue
        status = str(getattr(row, "status", "RECORDED") or "RECORDED").upper()
        if status in {"VOID", "NOT_MILKED"}:
            continue

        production_day = _as_day(
            getattr(row, "production_date", None)
            or getattr(row, "recorded_at", None)
        )
        if production_day is None or (as_of is not None and production_day > as_of):
            continue

        total = _milk_row_total(row)
        if total is not None:
            daily[production_day] += total

    ordered = sorted(daily.items(), key=lambda item: item[0])
    flagged_date = as_of.isoformat() if as_of is not None else None

    if not ordered:
        return {
            "finding_id": finding.finding_id,
            "animal_id": animal_id,
            "flagged_date": flagged_date,
            "prior_3_day_avg_litres": None,
            "current_yield_litres": None,
            "drop_variance_percent": None,
            "drop_variance_litres": None,
            "status": "DATA_UNAVAILABLE",
        }

    current_date, current_yield = ordered[-1]
    prior = ordered[-4:-1]

    if len(prior) < 3:
        return {
            "finding_id": finding.finding_id,
            "animal_id": animal_id,
            "flagged_date": current_date.isoformat(),
            "prior_3_day_avg_litres": None,
            "current_yield_litres": round(current_yield, 2),
            "drop_variance_percent": None,
            "drop_variance_litres": None,
            "status": "INSUFFICIENT_PRIOR_COMPLETE_DAYS",
        }

    prior_average = sum(value for _, value in prior) / 3.0
    drop_litres = max(0.0, prior_average - current_yield)
    drop_percent = (
        (drop_litres / prior_average) * 100.0
        if prior_average > 0
        else None
    )

    severity = "UNKNOWN"
    if drop_percent is not None:
        severity = (
            "RED"
            if drop_percent >= 20.0
            else "YELLOW"
            if drop_percent >= 15.0
            else "GREEN"
        )

    return {
        "finding_id": finding.finding_id,
        "animal_id": animal_id,
        "flagged_date": current_date.isoformat(),
        "prior_3_day_dates": [day.isoformat() for day, _ in prior],
        "prior_3_day_avg_litres": round(prior_average, 2),
        "current_yield_litres": round(current_yield, 2),
        "drop_variance_percent": (
            round(drop_percent, 1)
            if drop_percent is not None
            else None
        ),
        "drop_variance_litres": round(drop_litres, 2),
        "severity": severity,
        "watchlist_threshold_percent": 15.0,
        "critical_threshold_percent": 20.0,
        "status": "CALCULATED",
    }


@router.get("")
def list_findings(module: str | None = None, status: str | None = None, severity: str | None = None):
    service, rf = _service()
    try:
        findings = service.list(module=module, status=status, severity=severity)
        return {"findings": [_finding_dict(f, service) for f in findings]}
    finally:
        rf.close()


@router.get("/counts")
def finding_counts():
    service, rf = _service()
    try:
        return {"counts": service.counts_by_module()}
    finally:
        rf.close()


@router.get("/{finding_id}/yield-drop-detail")
def yield_drop_finding_detail(finding_id: str):
    service, rf = _service()
    try:
        finding = service.repository.get_by_finding_id(finding_id)
        if finding is None:
            raise HTTPException(status_code=404, detail=f"No finding with id {finding_id}")
        return _yield_drop_detail(finding, rf)
    finally:
        rf.close()


@router.post("/{finding_id}/acknowledge")
def acknowledge_finding(finding_id: str, payload: AcknowledgeFindingRequest):
    service, rf = _service()
    try:
        return _finding_dict(service.acknowledge(finding_id, operator=payload.operator), service)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        rf.close()


@router.post("/{finding_id}/resolve")
def resolve_finding(finding_id: str, payload: ResolveFindingRequest):
    service, rf = _service()
    try:
        return _finding_dict(
            service.resolve(
                finding_id,
                operator=payload.operator,
                resolution_note=payload.resolution_note,
            ),
            service,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.post("/{finding_id}/reinstate")
def reinstate_finding(finding_id: str, payload: ReinstateFindingRequest):
    service, rf = _service()
    try:
        return _finding_dict(
            service.reinstate(
                finding_id,
                operator=payload.operator,
                reason=payload.reason,
            ),
            service,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()

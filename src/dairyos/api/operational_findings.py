"""Operational Finding lifecycle endpoints (AA-013 §4, D-UI-5).

Findings are raised by detection engines (e.g. the milk drop detector),
never created directly by an operator POST -- there is deliberately no
`POST /farm/findings`, the same way there is no manual way to create a
command-center decision. Operators can only acknowledge or resolve.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)

router = APIRouter(prefix="/farm/findings", tags=["Operational Findings"])


class AcknowledgeFindingRequest(BaseModel):
    operator: str = Field(default="UI Operator", min_length=1)


class ResolveFindingRequest(BaseModel):
    operator: str = Field(default="UI Operator", min_length=1)
    resolution_note: str | None = None


def _finding_dict(finding) -> dict[str, Any]:
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
    }


def _service() -> tuple[OperationalFindingService, RepositoryFactory]:
    rf = RepositoryFactory.create()
    return OperationalFindingService(rf.operational_findings()), rf


@router.get("")
def list_findings(module: str | None = None, status: str | None = None, severity: str | None = None):
    service, rf = _service()
    try:
        findings = service.list(module=module, status=status, severity=severity)
        return {"findings": [_finding_dict(f) for f in findings]}
    finally:
        rf.close()


@router.get("/counts")
def finding_counts():
    """Per-module unresolved counts for the dashboard nav badges (§4.5)."""

    service, rf = _service()
    try:
        return {"counts": service.counts_by_module()}
    finally:
        rf.close()


@router.post("/{finding_id}/acknowledge")
def acknowledge_finding(finding_id: str, payload: AcknowledgeFindingRequest):
    service, rf = _service()
    try:
        finding = service.acknowledge(finding_id, operator=payload.operator)
        return _finding_dict(finding)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        rf.close()


@router.post("/{finding_id}/resolve")
def resolve_finding(finding_id: str, payload: ResolveFindingRequest):
    service, rf = _service()
    try:
        finding = service.resolve(finding_id, operator=payload.operator, resolution_note=payload.resolution_note)
        return _finding_dict(finding)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()

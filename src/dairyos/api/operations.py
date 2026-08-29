from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container
from dairyos.operations.health.services.operations_health_service import (
    OperationsHealthService,
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


def get_state(container):
    return container.farm_operational_state_service.get_state()


def get_decisions(container):
    service = getattr(container, "operational_decision_service", None)
    if service is None:
        return []
    return list(service.evaluate() or [])


def get_finding_metrics(container):
    factory = getattr(container, "repository_factory", None)
    accessor = getattr(factory, "operational_findings", None)
    if not callable(accessor):
        return {"total": 0, "open": 0, "resolved": 0}
    repository = accessor()
    findings = list(repository.get_all() or [])
    resolved = sum(
        1
        for finding in findings
        if str(getattr(finding, "status", "")).upper() == "RESOLVED"
    )
    return {"total": len(findings), "open": len(findings) - resolved, "resolved": resolved}


def get_health_snapshot(container):
    state = get_state(container)
    decisions = get_decisions(container)
    finding_metrics = get_finding_metrics(container)
    attention_items = list(getattr(state, "exceptions", [],) or [])
    health_service = OperationsHealthService()
    return health_service.generate_snapshot(
        operational_state=state,
        attention_items=attention_items,
        decisions=decisions,
        active_decisions=len(decisions),
        pending_actions=sum(
            1 for decision in decisions
            if isinstance(decision, dict) and decision.get("owner_action_required", False)
        ),
        tracked_outcomes=finding_metrics["resolved"],
        learning_signals=0,
    )


def health_state(container):
    return get_health_snapshot(container).health_status


def attention_count(container):
    return len(get_decisions(container))


def critical_attention_count(container):
    return sum(
        1 for decision in get_decisions(container)
        if isinstance(decision, dict)
        and str(decision.get("priority", "")).upper() == "CRITICAL"
    )


@router.get("/commands/status")
def command_status(container=Depends(get_container)):
    decisions = get_decisions(container)
    attention = len(decisions)
    critical = sum(
        1 for decision in decisions
        if isinstance(decision, dict)
        and str(decision.get("priority", "")).upper() == "CRITICAL"
    )
    return {
        "health_status": health_state(container),
        "runtime": "ACTIVE",
        "events": container.event_journal.count(),
        "active_attention_count": attention,
        "has_critical_attention": critical > 0,
    }


@router.get("/dashboard")
def operations_dashboard(container=Depends(get_container)):
    state = get_state(container)
    decisions = get_decisions(container)
    snapshot = get_health_snapshot(container)
    finding_metrics = get_finding_metrics(container)
    total_findings = finding_metrics["total"]
    resolution_rate = 100.0 * finding_metrics["resolved"] / total_findings if total_findings else 0.0
    return {
        "health": snapshot.health_status,
        "farm_status": state.operational_status(),
        "milk_today": state.milk_total(),
        "feed_today": state.feed_total(),
        "total_events": container.event_journal.count(),
        "open_issues": len(decisions),
        "open_findings": finding_metrics["open"],
        "resolved_findings": finding_metrics["resolved"],
        "total_findings": total_findings,
        "resolution_rate": round(resolution_rate, 2),
        "effectiveness_score": snapshot.operational_score,
    }


@router.get("/executive")
def executive(container=Depends(get_container)):
    state = get_state(container)
    decisions = get_decisions(container)
    snapshot = get_health_snapshot(container)
    finding_metrics = get_finding_metrics(container)
    attention = len(decisions)
    critical = sum(
        1 for decision in decisions
        if isinstance(decision, dict)
        and str(decision.get("priority", "")).upper() == "CRITICAL"
    )
    if critical > 0:
        recommended_focus = "Resolve critical operational decisions"
    elif attention > 0:
        recommended_focus = "Resolve active operational decisions"
    else:
        recommended_focus = "Continue normal operations"
    total_findings = finding_metrics["total"]
    resolution_rate = 100.0 * finding_metrics["resolved"] / total_findings if total_findings else 0.0
    return {
        "health_status": snapshot.health_status,
        "operational_status": state.operational_status(),
        "management_attention_required": snapshot.owner_attention_required,
        "owner_action_required": snapshot.owner_attention_required,
        "attention_count": attention,
        "critical_issue_count": critical,
        "recommended_focus": recommended_focus,
        "operational_priority_score": snapshot.operational_score,
        "total_events": container.event_journal.count(),
        "open_findings": finding_metrics["open"],
        "resolved_findings": finding_metrics["resolved"],
        "total_findings": total_findings,
        "resolution_rate": round(resolution_rate, 2),
    }


@router.get("/health")
def operations_health(container=Depends(get_container)):
    snapshot = get_health_snapshot(container)
    return {
        "health_status": snapshot.health_status,
        "operational_score": snapshot.operational_score,
        "owner_attention_required": snapshot.owner_attention_required,
        "runtime": "ACTIVE",
    }

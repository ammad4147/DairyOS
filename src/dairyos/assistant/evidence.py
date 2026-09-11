"""Typed evidence aggregation for the DairyOS AI Assistant.

Each aggregator owns one evidence family.  The controller can therefore add a
new read authority without teaching one large response mutator about every
domain.  The functions are deterministic and never perform a database write.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from dairyos.assistant.contracts import (
    DataQualityItem,
    EvidenceItem,
    NextAction,
    SourceMode,
)


@dataclass
class ResponseDraft:
    answer_type: str = "INFORMATION"
    scope: str = "AI Assistant"
    title: str = "AI Assistant"
    answer: str = ""
    expanded_explanation: str = ""
    source_mode: SourceMode = "LIVE_ONLY"
    database_read: bool = False
    safety: str = ""
    preconditions: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    expected_result: str = ""
    next_actions: list[NextAction] = field(default_factory=list)
    exceptions_recovery: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    role_guidance: dict[str, str] = field(default_factory=dict)
    selected_role_guidance: str = ""
    sources: list[str] = field(default_factory=list)
    related: list[dict[str, Any]] = field(default_factory=list)
    matched_items: list[dict[str, Any]] = field(default_factory=list)
    review: dict[str, Any] | None = None
    coverage: dict[str, Any] | None = None
    evidence: list[EvidenceItem] = field(default_factory=list)
    data_quality: list[DataQualityItem] = field(default_factory=list)


def _action(
    kind: str,
    label: str,
    description: str,
    *,
    target: str | None = None,
) -> NextAction:
    return NextAction(
        kind=kind,  # type: ignore[arg-type]
        label=label,
        description=description,
        target=target,
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _nested(value: dict[str, Any]) -> dict[str, Any]:
    nested = value.get("evidence")
    return nested if isinstance(nested, dict) else value


def _status(value: dict[str, Any], *, reference: bool = False) -> tuple[str, str]:
    if reference:
        return "REFERENCE_ONLY", "REFERENCE_ONLY"
    if value.get("available") is False:
        return "UNAVAILABLE", "UNAVAILABLE"
    status_text = str(value.get("data_status") or value.get("status") or "").upper()
    if status_text.startswith(("NO_", "UNAVAILABLE", "MISSING")):
        return "UNAVAILABLE", "UNAVAILABLE"
    if status_text.startswith(("INCOMPLETE", "PARTIAL", "WARNING")):
        return "PARTIAL", "PARTIAL"
    if str(value.get("overall") or "").upper() == "FAIL":
        return "PARTIAL", "PARTIAL"
    return "AVAILABLE", "VERIFIED"


def _record_count(value: dict[str, Any]) -> int | None:
    nested = _nested(value)
    for key in ("record_count", "transaction_count", "health_case_count"):
        candidate = value.get(key, nested.get(key))
        if isinstance(candidate, int) and candidate >= 0:
            return candidate
    return None


def _source_tables(value: dict[str, Any]) -> list[str]:
    nested = _nested(value)
    tables = value.get("source_tables") or nested.get("source_tables") or []
    return [str(item) for item in tables if item]


def _summary(tool_name: str, value: dict[str, Any]) -> str:
    nested = _nested(value)
    if value.get("available") is False:
        return f"{tool_name} was unavailable: {value.get('error') or 'unknown error'}."
    metric = str(value.get("metric") or nested.get("metric") or tool_name)
    if metric == "milk_production":
        return f"Milk production evidence: {nested.get('total_litres', 'unavailable')} litres."
    if metric == "reproduction_and_calf_lifecycle":
        return (
            f"Calving events: {nested.get('actual_calving_events', 0)}; "
            f"calf records: {nested.get('calf_animal_records', 0)}."
        )
    if metric == "mortality":
        return (
            f"Mortality events: {nested.get('mortality_events', 0)}; "
            f"current deceased records: {nested.get('currently_deceased_animals', 0)}."
        )
    if metric == "health_insight":
        return (
            f"Health observations: {nested.get('matching_observation_count', 0)}; "
            f"possible conditions: {len(nested.get('probable_conditions') or [])}."
        )
    if metric == "database_schema":
        return f"Database schema evidence for {value.get('table_count', 0)} table(s)."
    if tool_name == "read_cop_metrics":
        return (
            f"COP/L status {value.get('status') or value.get('data_status') or 'UNKNOWN'} "
            f"for {((value.get('period') or {}).get('effective_start'))} to "
            f"{((value.get('period') or {}).get('effective_end'))}."
        )
    if tool_name == "read_operational_logs":
        logs = value.get("database_logs") or {}
        return (
            f"Persistent journal entries: {len(logs.get('event_journal') or [])}; "
            f"operational events: {len(logs.get('operational_events') or [])}."
        )
    return f"Read-only {metric.replace('_', ' ')} evidence was returned."


def evidence_item(
    tool_name: str,
    value: dict[str, Any],
    *,
    index: int = 0,
) -> EvidenceItem:
    """Convert one bounded tool result into an inspectable typed item."""

    source = {
        "search_knowledge_base": "knowledge_base",
        "read_system_snapshot": "system_snapshot",
        "read_system_health": "system_health",
        "read_command_center": "command_center",
        "read_operational_data": "operational_data",
        "read_cop_metrics": "cop_metrics",
        "read_health_insight": "health_insight",
        "read_operational_logs": "operational_logs",
        "read_database_schema": "database_schema",
        "read_safety_policy": "safety_policy",
    }.get(tool_name, tool_name)
    reference = tool_name == "search_knowledge_base"
    status, quality = _status(value, reference=reference)
    nested = _nested(value)
    title = {
        "knowledge_base": "Local grounded knowledge",
        "system_snapshot": "Current runtime snapshot",
        "system_health": "System health checks",
        "command_center": "Operational Command Center",
        "operational_data": "Persisted operational data",
        "cop_metrics": "Persisted COP/L authority",
        "health_insight": "Persisted health and veterinary evidence",
        "operational_logs": "Persistent operational logs",
        "database_schema": "Current application database schema",
        "safety_policy": "AI Assistant safety boundary",
    }.get(source, source.replace("_", " ").title())
    return EvidenceItem(
        id=f"{source}-{index + 1}",
        source=source,
        title=title,
        summary=_summary(tool_name, value),
        status=status,  # type: ignore[arg-type]
        data_quality_status=quality,  # type: ignore[arg-type]
        read_only=value.get("read_only") is not False,
        database_read=bool(value.get("database_read")),
        source_tables=_source_tables(value),
        period=value.get("period") if isinstance(value.get("period"), dict) else None,
        record_count=_record_count(value),
        pagination=(
            value.get("pagination")
            if isinstance(value.get("pagination"), dict)
            else nested.get("pagination")
            if isinstance(nested.get("pagination"), dict)
            else None
        ),
        details=_json_safe(value),
    )


def _quality_for(
    source: str,
    value: dict[str, Any],
    *,
    reference: bool = False,
) -> DataQualityItem:
    _, quality = _status(value, reference=reference)
    if quality == "VERIFIED":
        message = "Read from the current persisted authority under a read-only boundary."
    elif quality == "PARTIAL":
        message = "Evidence is available but incomplete; the answer preserves the missing or warning status."
    elif quality == "UNAVAILABLE":
        message = str(value.get("error") or value.get("data_status") or "Live evidence was unavailable.")
    else:
        message = "Grounded reference guidance; it is not a live operational measurement."
    return DataQualityItem(source=source, status=quality, message=message)  # type: ignore[arg-type]


def _base_live(
    *,
    answer_type: str,
    scope: str,
    title: str,
    answer: str,
    explanation: str,
    safety: str,
    effects: list[str] | None = None,
    source_mode: SourceMode = "LIVE_ONLY",
) -> ResponseDraft:
    return ResponseDraft(
        answer_type=answer_type,
        scope=scope,
        title=title,
        answer=answer,
        expanded_explanation=explanation,
        source_mode=source_mode,
        database_read=True,
        safety=safety,
        effects=effects or ["No operational record was changed."],
    )


def aggregate_system_health(value: dict[str, Any]) -> ResponseDraft:
    checks = value.get("checks") or []
    failed = [
        str(item.get("name"))
        for item in checks
        if isinstance(item, dict) and item.get("status") == "FAIL"
    ]
    warnings = [
        str(item.get("name"))
        for item in checks
        if isinstance(item, dict) and item.get("status") == "WARNING"
    ]
    overall = str(value.get("overall") or "UNKNOWN")
    draft = _base_live(
        answer_type="LIVE_SYSTEM_HEALTH",
        scope="Current DairyOS runtime and persisted data integrity",
        title="Read-only DairyOS system health",
        answer=(
            f"System Health is {overall}. The check recorded {len(failed)} failure(s) "
            f"and {len(warnings)} warning(s)."
        ),
        explanation=(
            "The report includes database responsiveness, current schema and canonical columns, "
            "persistence visibility, event/outbox linkage, clinical record links, backup protection, "
            "managed data layout, AI Assistant knowledge availability and runtime state. "
            + ("Failures: " + ", ".join(failed) + ". " if failed else "")
            + ("Warnings: " + ", ".join(warnings) + "." if warnings else "")
        ),
        safety=value.get(
            "safety",
            "System health is diagnostic and read-only; it does not repair or reset DairyOS.",
        ),
        effects=["Only diagnostic evidence was read; no system or farm record was changed."],
    )
    draft.next_actions = [
        _action(
            "review_evidence",
            "Review failed or warning checks",
            "Inspect the itemized system-health evidence before taking any separate authorised remediation.",
        )
    ]
    draft.data_quality = [
        DataQualityItem(
            source="system_health",
            status="VERIFIED" if not failed else "PARTIAL",
            message=(
                "All reported checks completed."
                if not failed
                else "The health report completed but contains failed checks."
            ),
        )
    ]
    return draft


def aggregate_cop(value: dict[str, Any]) -> ResponseDraft:
    period = value.get("period") or {}
    label = f"{period.get('effective_start')} to {period.get('effective_end')}"
    status = value.get("status") or value.get("data_status")
    if status == "OK":
        draft = _base_live(
            answer_type="LIVE_OPERATIONAL_DATA",
            scope="Persisted DairyOS COP authority",
            title="COP/L from persisted DairyOS data",
            answer=(
                f"For the completed period {label}, the governed period COP/L is "
                f"{value.get('period_cop_per_litre')}. The average daily COP/L is "
                f"{value.get('average_daily_cop_per_litre')}, and the maximum daily COP/L is "
                f"{value.get('maximum_daily_cop_per_litre')}."
            ),
            explanation=(
                f"This uses {value.get('valid_daily_days')} complete daily authority rows and "
                f"{value.get('period_milk_litres')} litres of persisted milk. The period figure is "
                "weighted by milk volume; average and maximum are daily statistics. "
                f"{value.get('calculation_basis')}."
            ),
            safety=(
                "Live operational values were read without writes. Missing or incomplete authority "
                "is never represented as zero."
            ),
            effects=["No operational record was changed; only persisted authorities were read."],
        )
        draft.preconditions = ["The requested dates are limited to completed operational days."]
        draft.steps = [
            "Read the governed TMR snapshots, attributed Finance OPEX and milk ledger.",
            "Recompute the period and daily statistics from those persisted authorities.",
        ]
        draft.expected_result = "A traceable COP/L answer with its period, daily coverage and data basis."
        draft.next_actions = [
            _action(
                "ask_follow_up",
                "Request another COP/L view",
                "Ask for a different month, date range or daily COP/L breakdown.",
            )
        ]
        draft.data_quality = [
            DataQualityItem(
                source="cop_metrics",
                status="VERIFIED",
                message="Complete daily cost authority and milk denominator were available for the reported period.",
            )
        ]
        return draft

    missing = ", ".join(value.get("missing_authority_days") or []) or "none"
    draft = _base_live(
        answer_type="LIVE_OPERATIONAL_DATA_INCOMPLETE",
        scope="Persisted DairyOS COP authority",
        title="COP/L authority is incomplete",
        answer=(
            f"I cannot provide a defensible COP/L for {label}. The persisted cost authority is "
            f"{status}; missing authority days: {missing}. I did not substitute zero."
        ),
        explanation=(
            "DairyOS keeps missing historical TMR authority unavailable rather than converting it to a zero cost. "
            "The response remains read-only and identifies the exact days that prevent a complete calculation."
        ),
        safety=(
            "Live operational values were read without writes. Missing or incomplete authority is never represented as zero."
        ),
        effects=["Incomplete COP/L is surfaced as unavailable instead of being miscalculated."],
    )
    draft.next_actions = [
        _action(
            "review_evidence",
            "Review missing cost authority",
            "Inspect the listed dates and restore the governed historical authority through the authorised operating workflow.",
        )
    ]
    draft.data_quality = [
        DataQualityItem(
            source="cop_metrics",
            status="PARTIAL",
            message=f"Missing or incomplete cost authority dates: {missing}.",
        )
    ]
    return draft


def aggregate_health(value: dict[str, Any]) -> ResponseDraft:
    candidates = value.get("probable_conditions") or []
    boundary = value.get("assessment_boundary") or (
        "These are educational differentials only. A veterinarian must examine the animal, "
        "confirm the diagnosis, choose treatment, dose and withdrawal, and record the authorised plan."
    )
    if value.get("history_requested"):
        evidence_animal_ids = [
            str(item)
            for item in value.get("animal_ids_with_health_evidence") or []
            if item
        ]
        animal_note = ""
        requested_sick_list = bool(value.get("sick_list_requested"))
        if requested_sick_list:
            active_ids = [
                str(item)
                for item in value.get("current_sick_animal_ids")
                or value.get("active_sick_animal_ids")
                or []
                if item
            ]
            observation_ids = [
                str(item)
                for item in value.get("open_health_observation_animal_ids") or []
                if item
            ]
            animal_note = (
                " Active sick animal IDs (open health cases): "
                + (", ".join(active_ids[:20]) or "none")
                + "."
            )
            if observation_ids:
                animal_note += (
                    " Open health-observation IDs requiring case review: "
                    + ", ".join(observation_ids[:20])
                    + "."
                )
        elif evidence_animal_ids:
            shown = ", ".join(evidence_animal_ids[:20])
            remaining = len(evidence_animal_ids) - len(evidence_animal_ids[:20])
            animal_note = f" Animals with persisted health evidence: {shown}."
            if remaining > 0:
                animal_note += f" {remaining} additional animal ID(s) are in the evidence panel."
        draft = _base_live(
            answer_type="LIVE_OPERATIONAL_DATA",
            scope="Persisted DairyOS health history",
            title="Health history from persisted records",
            answer=(
                f"The selected period contains {value.get('health_case_count', 0)} persisted health case(s), "
                f"{value.get('matching_observation_count', 0)} health observation(s), and "
                f"{value.get('treatment_count', 0)} treatment record(s)."
                + animal_note
            ),
            explanation=(
                "Health cases, observations and treatments are reported as separate persisted authorities. "
                "A health case is not inferred from an observation, and a treatment is not treated as a confirmed diagnosis. "
                "Bounded records and the selected period are available in the read-only evidence."
            ),
            safety=boundary,
            effects=["No health, treatment or case record was changed."],
        )
        draft.data_quality = [
            DataQualityItem(
                source="health_insight",
                status="VERIFIED",
                message="Health cases, observations and treatments were counted from their separate persisted authorities.",
            )
        ]
        return draft
    if candidates:
        names = ", ".join(str(item.get("condition")) for item in candidates[:3])
        management = "; ".join(
            str(item.get("treatment_guidance") or item.get("management_guidance"))
            for item in candidates[:2]
            if item.get("treatment_guidance") or item.get("management_guidance")
        )
        diagnostic = "; ".join(
            ", ".join(str(step) for step in item.get("diagnostic_path") or [])
            for item in candidates[:2]
            if item.get("diagnostic_path")
        )
        urgent = "; ".join(
            ", ".join(str(sign) for sign in item.get("urgent_signs") or [])
            for item in candidates[:2]
            if item.get("urgent_signs")
        )
        draft = _base_live(
            answer_type="LIVE_HEALTH_INSIGHT",
            scope="Persisted health evidence and vetted veterinary reference",
            title="Probable health conditions to assess",
            answer=(
                f"The entered signs are compatible with these possible conditions: {names}. "
                "They are differentials for veterinary assessment, not a confirmed diagnosis. "
                f"Initial treatment/management guidance: {management or 'seek veterinary assessment promptly.'}"
            ),
            explanation=(
                f"The Assistant found {value.get('matching_observation_count', 0)} matching persisted health observations "
                f"and {value.get('treatment_count', 0)} persisted treatments. Diagnostic path: "
                f"{diagnostic or 'veterinarian-directed examination and testing.'} Urgent signs to escalate: "
                f"{urgent or 'any systemic deterioration.'} Review the candidate evidence, then have the responsible "
                "veterinarian examine the animal and record the authorised plan."
            ),
            safety=boundary,
            effects=["Only read-only health and reference evidence was used; no treatment was prescribed or recorded."],
        )
        draft.preconditions = [
            "Protect animal welfare and capture objective signs, timing and animal identity."
        ]
        draft.steps = [
            "Review the probable-condition cards and urgent signs.",
            "Obtain veterinarian-directed examination/testing.",
            "Record the confirmed diagnosis, authorised treatment, dose and withdrawal period in DairyOS.",
        ]
        draft.expected_result = "A safe differential assessment with traceable clinical evidence and professional escalation."
        draft.next_actions = [
            _action(
                "contact_veterinarian",
                "Escalate to the veterinarian",
                "Escalate urgent or systemic deterioration immediately; the Assistant does not confirm a diagnosis or prescribe treatment.",
            ),
            _action(
                "ask_follow_up",
                "Narrow to one animal",
                "Ask for one animal ID to narrow the persisted health evidence.",
            ),
        ]
        draft.data_quality = [
            DataQualityItem(
                source="health_insight",
                status="VERIFIED",
                message="Possible conditions are grounded in the local reference and separated from persisted observations.",
            )
        ]
        return draft
    draft = _base_live(
        answer_type="HEALTH_REFERENCE_NO_MATCH",
        scope="Persisted health evidence and vetted veterinary reference",
        title="No sufficiently grounded health differential",
        answer="I could not match the entered signs to a sufficiently grounded disease-reference candidate.",
        explanation=(
            "Record objective observations and seek veterinarian-directed examination; the Assistant will not invent a diagnosis or prescribe treatment."
        ),
        safety=boundary,
    )
    draft.next_actions = [
        _action(
            "contact_veterinarian",
            "Seek veterinary assessment",
            "Record objective signs and obtain a veterinarian-directed examination.",
        )
    ]
    draft.data_quality = [
        DataQualityItem(
            source="health_insight",
            status="PARTIAL",
            message="No sufficiently grounded reference candidate matched the entered signs.",
        )
    ]
    return draft


def aggregate_schema(value: dict[str, Any]) -> ResponseDraft:
    selected = value.get("selected_table")
    if isinstance(selected, dict):
        table_name = selected.get("table") or "the selected table"
        columns = selected.get("columns") or []
        answer = (
            f"The current {table_name} table has {len(columns)} column(s) and "
            f"{selected.get('row_count', 0)} persisted row(s). Its bounded read-only rows and column definitions are included in the evidence."
        )
        title = f"{table_name} schema from persisted database"
    else:
        tables = value.get("tables") or []
        names = [str(item.get("table")) for item in tables if isinstance(item, dict) and item.get("table")]
        answer = (
            f"The current DairyOS database contains {value.get('table_count', len(tables))} table(s): "
            f"{', '.join(names) or 'none'}. Full column definitions, row counts and any bounded selected rows are included in the read-only evidence."
        )
        title = "Current DairyOS database schema"
    draft = _base_live(
        answer_type="LIVE_OPERATIONAL_DATA_SCHEMA",
        scope="Current DairyOS application database schema",
        title=title,
        answer=answer,
        explanation=(
            "The schema was inspected from the current DairyOS database without changing any row, index or definition. "
            "Credential-like values are omitted or redacted."
        ),
        safety="The current DairyOS database schema was inspected through a transaction-scoped read-only guard.",
        effects=["No database table row, schema definition or credential was changed."],
    )
    draft.next_actions = [
        _action(
            "ask_follow_up",
            "Inspect a table",
            "Ask for a specific table name when bounded rows or a selected period are required.",
        )
    ]
    draft.data_quality = [
        DataQualityItem(
            source="database_schema",
            status="VERIFIED",
            message="The catalog and selected schema were read from the current application database.",
        )
    ]
    return draft


def _operational_summary(item: dict[str, Any]) -> str:
    metric = item.get("metric")
    if metric == "reproduction_and_calf_lifecycle":
        return f"{item.get('actual_calving_events')} calving event(s) and {item.get('calf_animal_records')} calf record(s)"
    if metric == "mortality":
        return f"{item.get('mortality_events')} mortality event(s)"
    if metric == "milk_production":
        return f"{item.get('total_litres')} litres of milk production"
    if metric == "milk_dispositions":
        return f"{item.get('quantity_litres')} litres across {item.get('record_count')} milk dispositions"
    if metric == "health_insight":
        return f"{item.get('matching_observation_count', 0)} health observation(s)"
    return f"{item.get('record_count', 0)} {metric or 'operational'} record(s)"


def aggregate_operational_data(value: dict[str, Any]) -> ResponseDraft:
    evidence = value.get("evidence")
    if not isinstance(evidence, dict):
        evidence = value
    metric = evidence.get("metric")
    if metric == "operational_multi_domain":
        summaries = [
            _operational_summary(item)
            for item in evidence.get("evidence") or []
            if isinstance(item, dict)
        ]
        answer = "The selected period contains " + "; ".join(summaries) + "."
        title = "Combined operational answer from persisted data"
        explanation = "Each requested domain was read from its own persisted authority and kept distinct in the supporting evidence; no record was changed or silently omitted."
    elif metric == "operational_period_empty":
        answer = "The requested date range contains no completed operational day, so no live value was substituted."
        title = "No completed operational date in the requested period"
        explanation = "DairyOS does not turn an empty or future period into a fabricated zero. Ask for a completed operational date or another period."
    elif metric == "milk_production":
        answer = (
            f"Persisted DairyOS milk production for the requested period is {evidence.get('total_litres')} litres "
            f"across {evidence.get('days_with_production')} production days."
            if evidence.get("record_count") or evidence.get("missing_yield_records")
            else "No persisted milk production records were found for the requested period."
        )
        title = "Milk production from persisted records"
        explanation = "VOID and NOT_MILKED session statements were excluded, and entered session yields were summed according to the milk authority. The daily breakdown is included in the read-only tool result."
    elif metric == "reproduction_and_calf_lifecycle":
        answer = f"The selected period contains {evidence.get('actual_calving_events')} actual persisted calving event(s) and {evidence.get('calf_animal_records')} calf animal record(s)."
        title = "Calving and calf records from persisted data"
        explanation = "Actual calving events are classified from persisted breeding records; calf master records are reported separately because a birth event and an animal registration are different authorities."
    elif metric == "mortality":
        answer = f"The selected period contains {evidence.get('mortality_events')} persisted mortality event(s). The current animal master contains {evidence.get('currently_deceased_animals')} deceased animal record(s)."
        title = "Mortality from persisted records"
        explanation = "Mortality events are read from durable animal-disposition events; current deceased master records are shown separately so historical event counts are not confused with current state."
    elif metric == "finance_transactions":
        answer = f"The selected period contains {evidence.get('transaction_count')} Finance transaction(s): income {evidence.get('income_total')} and expenses {evidence.get('expense_total')}, for net cash flow {evidence.get('net_cash_flow')}."
        title = "Finance records from persisted data"
        explanation = "The answer reads persisted financial transactions and preserves their status and COP metadata in the supporting evidence. VOID and other inactive records are excluded from totals by the Finance classifier."
    elif metric == "feed_records":
        answer = f"The selected period contains {evidence.get('feed_record_count')} feed record(s), totalling {evidence.get('quantity_kg')} kg and recorded feed cost {evidence.get('recorded_feed_cost')}."
        title = "Feed records from persisted data"
        explanation = "This is the feed-record ledger. Governed historical COP uses immutable daily TMR cost snapshots, which are kept distinct from feeding events in the evidence response."
    elif metric == "animal_register":
        answer = f"The selected scope contains {evidence.get('animal_count')} persisted animal record(s)."
        title = "Animal records from persisted data"
        explanation = "The response includes lifecycle and status counts plus bounded animal records. Permanent animal identity and historical records remain intact; the read-only Assistant never deletes or changes an animal."
    elif metric == "milk_dispositions":
        answer = f"The selected period contains {evidence.get('record_count')} active milk disposition record(s) covering {evidence.get('quantity_litres')} litres. Recorded amount due is {evidence.get('amount_due')}, with {evidence.get('amount_received')} received."
        title = "Milk destinations from persisted data"
        explanation = "Disposition types and bounded sale/wastage records are included as supporting evidence. VOID rows are excluded from the totals."
    elif metric == "operational_input_events":
        answer = f"The selected period contains {evidence.get('record_count')} persisted {evidence.get('input_type')} input event(s)."
        title = "Operational input history from persisted events"
        explanation = "The event journal is the durable audit authority for this input type; VOID inputs are excluded and bounded payloads are redacted before display."
    elif metric == "operational_table":
        table_name = (evidence.get("table") or {}).get("table", "selected table")
        answer = f"The selected scope contains {evidence.get('record_count')} persisted record(s) in {table_name}."
        title = f"{table_name} records from persisted data"
        explanation = "The response contains bounded, sanitised rows and states whether a date column was used for the requested period. The database transaction was read-only."
    elif metric == "operational_tables":
        table_names = [
            str((item.get("table") or {}).get("table"))
            for item in evidence.get("tables") or []
            if isinstance(item, dict)
        ]
        answer = f"I read {evidence.get('record_count')} persisted record(s) across {', '.join(table_names)} in read-only mode."
        title = "Selected operational tables from persisted data"
        explanation = "Each table includes a bounded, sanitised record sample and its selected-period count where a date column is available."
    else:
        answer = "I read the current DairyOS operational data catalog in read-only mode. The tool result contains counts for the available domain authorities."
        title = "Current operational data catalog"
        explanation = "Use a specific area, date or table name to receive the corresponding bounded records and calculation. The database schema tool can enumerate every current table and its columns without exposing credentials."
    draft = _base_live(
        answer_type=(
            "LIVE_OPERATIONAL_DATA_UNAVAILABLE"
            if metric == "operational_period_empty"
            else "LIVE_OPERATIONAL_DATA_CATALOG"
            if metric == "operational_data_catalog"
            else "LIVE_OPERATIONAL_DATA"
        ),
        scope=(
            "Requested DairyOS operational period"
            if metric == "operational_period_empty"
            else "Current DairyOS application database"
            if metric == "operational_data_catalog"
            else "Persisted DairyOS operational authorities"
        ),
        title=title,
        answer=answer,
        explanation=explanation,
        safety=(
            "No live value was available for the requested period; no zero was invented."
            if metric == "operational_period_empty"
            else "The operational database was read through a transaction-scoped read-only guard."
        ),
    )
    draft.next_actions = [
        _action(
            "ask_follow_up",
            "Request a detailed view",
            "Ask for a specific date range, animal ID or table when the bounded records are required.",
        )
    ]
    draft.data_quality = [
        DataQualityItem(
            source="operational_data",
            status="UNAVAILABLE" if metric == "operational_period_empty" else "VERIFIED",
            message=(
                "No completed operational date was in the requested period."
                if metric == "operational_period_empty"
                else "Operational totals and records were read from the current persisted authorities."
            ),
        )
    ]
    return draft


def aggregate_logs(value: dict[str, Any]) -> ResponseDraft:
    logs = value.get("database_logs") or {}
    draft = _base_live(
        answer_type="LIVE_OPERATIONAL_LOGS",
        scope="Persisted DairyOS logs and runtime evidence",
        title="Operational log evidence",
        answer=(
            f"I read {len(logs.get('event_journal') or [])} persistent journal entries and "
            f"{len(logs.get('operational_events') or [])} operational-event entries, plus bounded local runtime log tails where available."
        ),
        explanation="The log evidence is bounded and sanitised for display. It is read inside the same database read-only transaction; no event, outbox row or file was changed.",
        safety="Logs are read-only and credential-like values are redacted.",
        effects=["Only log and audit evidence was read."],
    )
    draft.next_actions = [
        _action(
            "ask_follow_up",
            "Narrow the log window",
            "Provide a date range, event type or error text for a more focused read-only log review.",
        )
    ]
    draft.data_quality = [
        DataQualityItem(
            source="operational_logs",
            status="VERIFIED",
            message="Persistent journal and operational-event records were read with bounded, redacted payloads.",
        )
    ]
    return draft


def aggregate_unavailable(
    tool_context: dict[str, Any], preferred_tools: list[str] | tuple[str, ...]
) -> ResponseDraft:
    failed = [
        name
        for name in preferred_tools
        if isinstance(tool_context.get(name), dict)
        and tool_context[name].get("available") is False
    ]
    names = ", ".join(failed) or "the requested live authority"
    draft = _base_live(
        answer_type="LIVE_DATA_UNAVAILABLE",
        scope="Current DairyOS operational database or runtime logs",
        title="Live DairyOS data could not be read",
        answer=(
            f"I could not read the requested live DairyOS evidence because {names} was unavailable. "
            "I have not invented a value or changed any record."
        ),
        explanation="Current operational values must be retried after database or runtime readiness is restored. Any available bounded diagnostic evidence is listed separately.",
        safety="Live data is unavailable; no value was substituted or fabricated.",
    )
    draft.source_mode = "LIVE_UNAVAILABLE"
    draft.next_actions = [
        _action(
            "retry_live_data",
            "Retry after readiness is restored",
            "Restore DairyOS database/runtime readiness and ask the live-data question again.",
        )
    ]
    draft.data_quality = [
        DataQualityItem(
            source="live_authority",
            status="UNAVAILABLE",
            message=f"Unavailable live tool(s): {names}.",
        )
    ]
    return draft


def aggregate_knowledge(value: dict[str, Any]) -> ResponseDraft:
    if value.get("available") is False:
        return ResponseDraft(
            answer_type="INSUFFICIENT_COVERAGE",
            scope="AI Assistant knowledge corpus",
            title="Grounded knowledge was unavailable",
            answer="The local knowledge corpus could not be read, so I cannot provide a grounded guidance answer.",
            expanded_explanation=str(value.get("error") or "Retry after the packaged knowledge assets are available."),
            source_mode="KNOWLEDGE_ONLY",
            safety="No live data was read and no farm record was changed.",
            next_actions=[
                _action(
                    "retry_live_data",
                    "Retry the grounded question",
                    "Retry after the packaged local knowledge assets are available.",
                )
            ],
            data_quality=[
                DataQualityItem(
                    source="knowledge_base",
                    status="UNAVAILABLE",
                    message="The local grounded knowledge corpus was unavailable.",
                )
            ],
        )
    legacy_actions = [str(item) for item in value.get("next_actions") or []]
    actions = [
        _action("ask_follow_up", "Next step", item) for item in legacy_actions
    ]
    draft = ResponseDraft(
        answer_type=str(value.get("answer_type") or "INFORMATION"),
        scope=str(value.get("scope") or "DairyOS operational guidance"),
        title=str(value.get("title") or "AI Assistant guidance"),
        answer=str(value.get("answer") or ""),
        expanded_explanation=str(value.get("expanded_explanation") or ""),
        source_mode="KNOWLEDGE_ONLY",
        database_read=False,
        safety=str(value.get("safety") or "No live data was read and no farm record was changed."),
        preconditions=[str(item) for item in value.get("preconditions") or []],
        steps=[str(item) for item in value.get("steps") or []],
        expected_result=str(value.get("expected_result") or ""),
        next_actions=actions,
        exceptions_recovery=[str(item) for item in value.get("exceptions_recovery") or []],
        effects=[str(item) for item in value.get("effects") or []],
        role_guidance={str(k): str(v) for k, v in (value.get("role_guidance") or {}).items()},
        selected_role_guidance=str(value.get("selected_role_guidance") or ""),
        sources=[str(item) for item in value.get("sources") or []],
        related=value.get("related") or [],
        matched_items=value.get("matched_items") or [],
        review=value.get("review") if isinstance(value.get("review"), dict) else None,
        coverage=value.get("coverage") if isinstance(value.get("coverage"), dict) else None,
        data_quality=[
            DataQualityItem(
                source="knowledge_base",
                status="REFERENCE_ONLY",
                message="Grounded local guidance; it is not a live operational measurement.",
            )
        ],
    )
    return draft


def aggregate_tool_evidence(tool_context: dict[str, Any]) -> list[EvidenceItem]:
    return [
        evidence_item(name, value, index=index)
        for index, (name, value) in enumerate(tool_context.items())
        if isinstance(value, dict) and name != "read_safety_policy"
    ]


def aggregate_live_evidence(
    tool_context: dict[str, Any],
    preferred_tools: list[str] | tuple[str, ...] | None = None,
) -> ResponseDraft:
    """Select one typed domain aggregator while retaining every tool item."""

    preferred = list(preferred_tools or ())
    if not preferred:
        preferred = [
            "read_system_health",
            "read_cop_metrics",
            "read_health_insight",
            "read_database_schema",
            "read_operational_data",
            "read_operational_logs",
            "read_system_snapshot",
            "read_command_center",
        ]
    live_preferred = [name for name in preferred if name != "search_knowledge_base"]
    priority = {
        "read_system_health": 0,
        "read_cop_metrics": 1,
        "read_health_insight": 2,
        "read_database_schema": 3,
        "read_operational_data": 4,
        "read_operational_logs": 5,
        "read_system_snapshot": 6,
        "read_command_center": 7,
    }
    live_preferred.sort(key=lambda name: priority.get(name, 99))
    successful = [
        name
        for name in live_preferred
        if isinstance(tool_context.get(name), dict)
        and tool_context[name].get("available") is not False
    ]
    failed = [
        name
        for name in live_preferred
        if isinstance(tool_context.get(name), dict)
        and tool_context[name].get("available") is False
    ]
    if not successful and failed:
        draft = aggregate_unavailable(tool_context, live_preferred)
    else:
        selected = next(iter(successful), None)
        value = tool_context.get(selected) if selected else None
        if selected == "read_system_health" and isinstance(value, dict):
            draft = aggregate_system_health(value)
        elif selected == "read_cop_metrics" and isinstance(value, dict):
            draft = aggregate_cop(value)
        elif selected == "read_health_insight" and isinstance(value, dict):
            draft = aggregate_health(value)
        elif selected == "read_database_schema" and isinstance(value, dict):
            draft = aggregate_schema(value)
        elif selected == "read_operational_data" and isinstance(value, dict):
            draft = aggregate_operational_data(value)
        elif selected == "read_operational_logs" and isinstance(value, dict):
            draft = aggregate_logs(value)
        elif selected == "read_system_snapshot" and isinstance(value, dict):
            backup = value.get("backup_health") or {}
            draft = _base_live(
                answer_type="LIVE_SYSTEM_SNAPSHOT",
                scope="Current DairyOS runtime and backup protection",
                title="Current DairyOS runtime snapshot",
                answer=f"DairyOS is running version {value.get('version', {}).get('version', value.get('version'))}; backup protection is {backup.get('status', 'reported') if isinstance(backup, dict) else backup}.",
                explanation="This is a read-only runtime and backup snapshot. It does not repair, reset or change farm data.",
                safety="The runtime snapshot was read without writes.",
                effects=["No system or farm record was changed."],
            )
        elif selected == "read_command_center" and isinstance(value, dict):
            draft = _base_live(
                answer_type="LIVE_COMMAND_CENTER",
                scope="Current DairyOS operational Command Center",
                title="Current operational Command Center",
                answer="The current Command Center snapshot is included in the itemized evidence.",
                explanation="Command Center context was read without changing decisions, alerts or watchlists.",
                safety="Command Center evidence is read-only.",
                effects=["No command, alert or operational decision was changed."],
            )
        else:
            draft = aggregate_unavailable(tool_context, live_preferred)
    draft.evidence = aggregate_tool_evidence(tool_context)
    for name, value in tool_context.items():
        if isinstance(value, dict) and name != "read_safety_policy":
            draft.data_quality.append(
                _quality_for(
                    {
                        "search_knowledge_base": "knowledge_base",
                        "read_system_snapshot": "system_snapshot",
                        "read_system_health": "system_health",
                        "read_command_center": "command_center",
                        "read_operational_data": "operational_data",
                        "read_cop_metrics": "cop_metrics",
                        "read_health_insight": "health_insight",
                        "read_operational_logs": "operational_logs",
                        "read_database_schema": "database_schema",
                    }.get(name, name),
                    value,
                    reference=name == "search_knowledge_base",
                )
            )
    # Keep the response quality list deterministic when an error caused an
    # additional diagnostic iteration.
    unique: dict[tuple[str, str], DataQualityItem] = {}
    for item in draft.data_quality:
        unique[(item.source, item.status)] = item
    draft.data_quality = list(unique.values())
    return draft

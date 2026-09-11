"""Pure-Python request classification for the AI Assistant state machine.

This is intentionally bounded and deterministic.  It is not an LLM deciding
which backend operation to call.  The classifier only identifies the minimum
read-only authorities needed for the question; the state machine controls all
execution and limits retries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestClassification:
    route: str
    live_data_required: bool
    documentation_required: bool
    tools: tuple[str, ...]
    reason: str


_MONTH_WORDS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)

_SYSTEM_HEALTH_TERMS = (
    "system health",
    "system-health",
    "health check",
    "database integrity",
    "schema integrity",
    "readiness check",
)
_SNAPSHOT_TERMS = (
    "ready",
    "readiness",
    "backup",
    "version",
    "system status",
    "runtime status",
)
_COMMAND_CENTER_TERMS = (
    "command center",
    "alert",
    "decision",
    "watchlist",
)
_COP_TERMS = (
    "cop/l",
    "cop / l",
    "cop per litre",
    "cop per liter",
    "cost of production",
    "cost per litre",
    "cost per liter",
    "feed cost / l",
    "average cop",
    "maximum cop",
    "minimum cop",
)
_CLINICAL_TERMS = (
    "health",
    "health case",
    "health history",
    "symptom",
    "probable diagnosis",
    "diagnos",
    "disease",
    "treatment",
    "fever",
    "cough",
    "mastitis",
    "sick",
    "ill",
    "signs",
    "udder",
    "diarrhea",
    "diarrhoea",
    "lameness",
    "panting",
    "weakness",
    "swollen",
    "quarter",
    "flakes",
    "clots",
    "abnormal milk",
    "reduced yield",
    "off feed",
    "not eating",
    "nasal discharge",
    "labored breathing",
    "laboured breathing",
    "cannot rise",
    "unable to stand",
    "recumbent",
    "foul discharge",
    "vaginal discharge",
    "tremor",
    "bloat",
    "dehydration",
    "bloody milk",
    "hard quarter",
)
_HEALTH_HISTORY_TERMS = (
    "health case",
    "health cases",
    "health observation",
    "health observations",
    "health history",
    "treatment history",
    "treatment record",
    "treatment records",
    "treatments recorded",
    "observations recorded",
    "cases recorded",
    "sick animal",
    "sick animals",
    "ill animal",
    "ill animals",
    "current health",
    "health status",
    "open health",
    "active health",
)
_CLINICAL_GUIDANCE_TERMS = (
    "symptom",
    "probable diagnosis",
    "diagnos",
    "disease",
    "treatment for",
    "how to treat",
    "treatment should",
    "what treatment",
    "fever",
    "cough",
    "mastitis",
    "signs",
    "udder",
    "diarrhea",
    "diarrhoea",
    "lameness",
    "panting",
    "weakness",
    "swollen",
    "quarter",
    "flakes",
    "clots",
    "abnormal milk",
    "reduced yield",
    "off feed",
    "not eating",
    "nasal discharge",
    "labored breathing",
    "laboured breathing",
    "cannot rise",
    "unable to stand",
    "recumbent",
    "foul discharge",
    "vaginal discharge",
    "tremor",
    "bloat",
    "dehydration",
    "bloody milk",
    "hard quarter",
)
_LOG_TERMS = (
    "log",
    "event history",
    "audit trail",
    "trace",
    "error",
    "failure",
    "outbox",
    "projection",
)
_SCHEMA_TERMS = (
    "database",
    "db",
    "table",
    "schema",
    "all records",
    "everything",
)
_OPERATIONAL_TERMS = (
    "milk",
    "litre",
    "liter",
    "yield",
    "production",
    "calf",
    "calves",
    "calving",
    "delivered",
    "birth",
    "mortality",
    "mortalities",
    "deceased",
    "died",
    "death",
    "farm data",
    "operational data",
    "persisted",
    "actual records",
    "finance",
    "financial",
    "expense",
    "income",
    "cash",
    "opex",
    "feed",
    "feeding",
    "ration",
    "tmr",
    "animal",
    "herd",
    "cow",
    "cattle",
    "livestock",
    "breeding",
    "pregnancy",
    "insemination",
    "vaccin",
    "milk quality",
    "quality sample",
    "fat",
    "snf",
    "disposition",
    "sold",
    "sale",
    "wastage",
    "inventory",
    "stock level",
    "reorder",
    "equipment",
    "maintenance",
    "service event",
    "repair",
    "payroll",
    "workforce",
    "employee",
    "semen",
    "bull",
    "youngstock",
    "young stock",
    "weaning",
    "weight gain",
    "growth",
    "finding",
    "alert history",
    "watchlist history",
)
_LIVE_QUESTION_MARKERS = (
    "what was",
    "what is the current",
    "how many",
    "how much",
    "show",
    "list",
    "count",
    "recorded",
    "records",
    "current",
    "actual",
    "in ",
    "during ",
    "for ",
)
_DOCUMENTATION_MARKERS = (
    "how do i",
    "how can i",
    "how does",
    "what happens",
    "what should i",
    "what is dairyos",
    "what can dairyos",
    "checklist",
    "procedure",
    "sop",
    "guide",
    "architecture",
    "troubleshoot",
    "why is",
    "why does",
    "explain",
    "safe next steps",
)


def _has(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def has_period_reference(question: str) -> bool:
    lowered = str(question or "").lower()
    return bool(
        re.search(r"\b20\d{2}-\d{2}-\d{2}\b", lowered)
        or any(month in lowered for month in _MONTH_WORDS)
        or any(
            phrase in lowered
            for phrase in ("today", "yesterday", "this month", "last month")
        )
    )


def looks_like_follow_up(question: str, previous_context: str) -> bool:
    lowered = str(question or "").strip().lower()
    if not previous_context.strip():
        return False
    if any(
        lowered.startswith(prefix)
        for prefix in ("what about", "and ", "also ", "same ", "that ", "those ")
    ):
        return True
    if any(
        phrase in lowered
        for phrase in (
            "same period",
            "that period",
            "the same month",
            "by day",
            "daily breakdown",
            "more detail",
            "tell me more",
        )
    ):
        return True
    return any(term in lowered for term in ("average", "maximum", "minimum")) and any(
        term in previous_context.lower()
        for term in ("cop/l", "cost per litre", "cost per liter", "cop per")
    )


def classify_request(question: str, previous_context: str = "") -> RequestClassification:
    """Select bounded read authorities without retrieving knowledge by default."""

    cleaned = str(question or "").strip()
    lowered = cleaned.lower()
    routing_text = (
        f"{previous_context}\n{cleaned}".lower()
        if looks_like_follow_up(cleaned, previous_context)
        else lowered
    )

    system_health = _has(routing_text, _SYSTEM_HEALTH_TERMS)
    snapshot = system_health or _has(routing_text, _SNAPSHOT_TERMS)
    command_center = _has(routing_text, _COMMAND_CENTER_TERMS)
    cop = _has(routing_text, _COP_TERMS)
    clinical = _has(routing_text, _CLINICAL_TERMS) and not system_health
    logs = _has(routing_text, _LOG_TERMS)
    schema = _has(routing_text, _SCHEMA_TERMS)
    operational_domain = _has(routing_text, _OPERATIONAL_TERMS)
    data_question = _has(routing_text, _LIVE_QUESTION_MARKERS) or has_period_reference(
        routing_text
    )
    explicit_documentation = _has(routing_text, _DOCUMENTATION_MARKERS)

    # A workflow question such as "how do I record a milk entry" is guidance,
    # not a request to scan current milk rows.  Conversely, "what was milk in
    # July" has both a domain and a data marker and must use live authority.
    operational = operational_domain and data_question
    live_data = snapshot or command_center or cop or clinical or logs or schema or operational
    # A health-history/list/count request is live evidence, not a request for
    # disease-reference retrieval. Symptom, diagnosis and treatment guidance
    # still receives the local vetted clinical corpus.
    health_history = _has(routing_text, _HEALTH_HISTORY_TERMS)
    clinical_guidance = _has(routing_text, _CLINICAL_GUIDANCE_TERMS)
    documentation = explicit_documentation or (
        clinical
        and not health_history
        and (clinical_guidance or not data_question)
    )

    tools: list[str] = ["read_safety_policy"]

    def add(name: str) -> None:
        if name not in tools:
            tools.append(name)

    if snapshot:
        add("read_system_snapshot")
    if system_health:
        add("read_system_health")
    if command_center:
        add("read_command_center")
    if cop:
        add("read_cop_metrics")
    if clinical:
        add("read_health_insight")
    if logs:
        add("read_operational_logs")
    if operational and not clinical:
        add("read_operational_data")
    if schema:
        add("read_database_schema")

    if documentation or not live_data:
        add("search_knowledge_base")

    if clinical:
        route = "clinical"
        reason = "Clinical wording requires persisted health evidence and vetted reference guidance."
    elif live_data:
        route = "live"
        reason = "The question requests current or historical DairyOS evidence from read-only authorities."
    else:
        route = "knowledge"
        reason = "No live-data signal was found; use the local grounded knowledge corpus only."

    return RequestClassification(
        route=route,
        live_data_required=live_data,
        documentation_required=documentation,
        tools=tuple(tools),
        reason=reason,
    )

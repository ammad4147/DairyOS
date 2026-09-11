"""Local, safe Agentic RAG runtime for the DairyOS AI Assistant."""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from dairyos.assistant.knowledge import GroundedAssistant
from dairyos.assistant.operational import (
    read_cop_metrics,
    read_health_insight,
    read_operational_data,
    read_operational_logs,
)


@dataclass(frozen=True)
class AssistantTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., dict[str, Any]]

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


def _knowledge(question: str, role: str = "Operator") -> dict[str, Any]:
    return GroundedAssistant().answer(question, role)


def _coverage() -> dict[str, Any]:
    return GroundedAssistant().coverage()


def _safety() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_allowed": False,
        "note": "AI Assistant never authorises or performs farm-data writes.",
    }


def _system_snapshot() -> dict[str, Any]:
    from dairyos.api.system import backup_health, version

    return {"version": version(), "backup_health": backup_health(), "read_only": True}


def _system_health() -> dict[str, Any]:
    from dairyos.api.dependencies import get_container
    from dairyos.api.health import get_system_health

    return get_system_health(get_container())


def _command_center_snapshot() -> dict[str, Any]:
    from dairyos.api.dependencies import get_container

    container = get_container()
    return {
        "operational_command_center": container.operational_command_center_service.snapshot(),
        "read_only": True,
    }


def _read_cop(question: str = "", **arguments: Any) -> dict[str, Any]:
    return read_cop_metrics(question=question, **arguments)


def _read_data(question: str = "", **arguments: Any) -> dict[str, Any]:
    return read_operational_data(question=question, **arguments)


def _read_health(question: str = "", **arguments: Any) -> dict[str, Any]:
    return read_health_insight(question=question, **arguments)


def _read_logs(question: str = "", **arguments: Any) -> dict[str, Any]:
    return read_operational_logs(question=question, **arguments)


def _read_database_schema(
    table_name: str | None = None, limit: int = 50
) -> dict[str, Any]:
    from dairyos.assistant.operational import _read_database_schema as read_schema

    return read_schema(table_name=table_name, limit=limit)


def _date_reader_properties() -> dict[str, Any]:
    return {
        "question": {"type": "string"},
        "start_date": {"type": ["string", "null"], "description": "ISO date"},
        "end_date": {"type": ["string", "null"], "description": "ISO date"},
        "month": {"type": ["string", "integer", "null"]},
        "year": {"type": ["string", "integer", "null"]},
    }


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


def _has_period_reference(question: str) -> bool:
    lowered = str(question or "").lower()
    return bool(
        re.search(r"\b20\d{2}-\d{2}-\d{2}\b", lowered)
        or any(month in lowered for month in _MONTH_WORDS)
        or any(
            phrase in lowered
            for phrase in ("today", "yesterday", "this month", "last month")
        )
    )


def _looks_like_follow_up(question: str, previous_context: str) -> bool:
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


class AssistantToolRegistry:
    def __init__(self) -> None:
        obj = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        self._tools = {
            "search_knowledge_base": AssistantTool(
                "search_knowledge_base",
                "Retrieve grounded DairyOS procedures and implementation evidence.",
                {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "role": {"type": "string"},
                    },
                    "required": ["question"],
                    "additionalProperties": False,
                },
                _knowledge,
            ),
            "knowledge_coverage": AssistantTool(
                "knowledge_coverage",
                "Report indexed corpus coverage and validation status.",
                obj,
                _coverage,
            ),
            "read_safety_policy": AssistantTool(
                "read_safety_policy",
                "Explain the AI Assistant safety boundary.",
                obj,
                _safety,
            ),
            "read_system_snapshot": AssistantTool(
                "read_system_snapshot",
                "Read DairyOS version and backup protection status.",
                obj,
                _system_snapshot,
            ),
            "read_system_health": AssistantTool(
                "read_system_health",
                "Run the current DairyOS read-only integrity, schema, persistence, backup and Assistant readiness checks.",
                obj,
                _system_health,
            ),
            "read_command_center": AssistantTool(
                "read_command_center",
                "Read current operational Command Center context without changing decisions.",
                obj,
                _command_center_snapshot,
            ),
            "read_operational_data": AssistantTool(
                "read_operational_data",
                "Read current persisted DairyOS operational data and canonical domain summaries without writing.",
                {
                    "type": "object",
                    "properties": {
                        **_date_reader_properties(),
                        "table_name": {"type": ["string", "null"]},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                    "required": ["question"],
                    "additionalProperties": False,
                },
                _read_data,
            ),
            "read_cop_metrics": AssistantTool(
                "read_cop_metrics",
                "Read persisted milk, governed TMR feed cost and attributed Finance OPEX to calculate COP/L statistics.",
                {
                    "type": "object",
                    "properties": _date_reader_properties(),
                    "required": ["question"],
                    "additionalProperties": False,
                },
                _read_cop,
            ),
            "read_health_insight": AssistantTool(
                "read_health_insight",
                "Read persisted health evidence and retrieve probable disease differentials from the vetted veterinary corpus.",
                {
                    "type": "object",
                    "properties": {
                        **_date_reader_properties(),
                        "animal_id": {"type": ["string", "null"]},
                    },
                    "required": ["question"],
                    "additionalProperties": False,
                },
                _read_health,
            ),
            "read_operational_logs": AssistantTool(
                "read_operational_logs",
                "Read bounded persistent event-journal, operational-event, projection-outbox and local runtime log evidence.",
                {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "start_date": {
                            "type": ["string", "null"],
                            "description": "ISO date",
                        },
                        "end_date": {
                            "type": ["string", "null"],
                            "description": "ISO date",
                        },
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                    "required": ["question"],
                    "additionalProperties": False,
                },
                _read_logs,
            ),
            "read_database_schema": AssistantTool(
                "read_database_schema",
                "Inspect the current DairyOS database tables, columns, row counts and bounded rows without changing the database.",
                {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": ["string", "null"]},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                    "additionalProperties": False,
                },
                _read_database_schema,
            ),
        }

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            raise ValueError(f"Unknown AI Assistant tool: {name}")
        return self._tools[name].handler(**arguments)


@dataclass
class Conversation:
    messages: list[dict[str, str]] = field(default_factory=list)


class AgenticAssistant:
    def __init__(self) -> None:
        self.registry = AssistantToolRegistry()
        self._conversations: dict[str, Conversation] = {}
        self._lock = RLock()

    def ask(
        self, question: str, role: str = "Operator", conversation_id: str | None = None
    ) -> dict[str, Any]:
        conversation_id = conversation_id or str(uuid.uuid4())
        with self._lock:
            conversation = self._conversations.setdefault(
                conversation_id, Conversation()
            )
            previous_context = "\n".join(
                item["content"] for item in conversation.messages[-4:]
            )
            previous_user_question = next(
                (
                    item["content"]
                    for item in reversed(conversation.messages)
                    if item.get("role") == "user"
                ),
                "",
            )
            conversation.messages.append({"role": "user", "content": question})
            context = "\n".join(item["content"] for item in conversation.messages[-4:])
        lowered = question.lower()
        routing_text = (
            f"{previous_context}\n{question}".lower()
            if _looks_like_follow_up(question, previous_context)
            else lowered
        )
        plan = ["read_safety_policy"]

        def add_tool(name: str) -> None:
            if name not in plan:
                plan.append(name)

        system_health_request = any(
            phrase in routing_text
            for phrase in (
                "system health",
                "system-health",
                "health check",
                "database integrity",
                "schema integrity",
                "readiness check",
            )
        )
        if any(
            term in routing_text
            for term in ("ready", "readiness", "backup", "version", "system")
        ):
            add_tool("read_system_snapshot")
        if system_health_request:
            add_tool("read_system_health")
        if any(
            term in routing_text
            for term in ("command center", "alert", "decision", "action", "watchlist")
        ):
            add_tool("read_command_center")
        if any(
            term in routing_text
            for term in (
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
            )
        ):
            add_tool("read_cop_metrics")
        if any(
            term in routing_text
            for term in (
                "symptom",
                "probable diagnosis",
                "diagnos",
                "disease",
                "treatment",
                "health",
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
                "hot",
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
        ) and not system_health_request:
            add_tool("read_health_insight")
        if any(
            term in routing_text
            for term in (
                "log",
                "event history",
                "audit trail",
                "trace",
                "error",
                "failure",
                "outbox",
                "projection",
            )
        ):
            add_tool("read_operational_logs")
        if any(
            term in routing_text
            for term in (
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
        ):
            add_tool("read_operational_data")
        if any(
            term in routing_text
            for term in (
                "database",
                "db",
                "table",
                "schema",
                "all records",
                "everything",
            )
        ):
            add_tool("read_database_schema")
        add_tool("search_knowledge_base")
        safety = self.registry.execute(plan[0], {})
        tool_context: dict[str, Any] = {}
        for tool_name in plan[1:]:
            if tool_name == "search_knowledge_base":
                continue
            try:
                arguments: dict[str, Any] = {}
                if tool_name in {
                    "read_operational_data",
                    "read_cop_metrics",
                    "read_health_insight",
                    "read_operational_logs",
                }:
                    tool_question = question
                    if (
                        previous_user_question
                        and _looks_like_follow_up(question, previous_context)
                        and not _has_period_reference(question)
                    ):
                        tool_question = f"{previous_user_question}\n{question}"
                    arguments["question"] = tool_question
                tool_context[tool_name] = self.registry.execute(tool_name, arguments)
            except (
                FileNotFoundError,
                OSError,
                RuntimeError,
                SQLAlchemyError,
                TypeError,
                ValueError,
                HTTPException,
            ) as exc:  # graceful fallback keeps grounded answer available
                tool_context[tool_name] = {"available": False, "error": str(exc)}
        grounded = self.registry.execute(
            "search_knowledge_base", {"question": context, "role": role}
        )
        result = dict(grounded)
        _apply_live_evidence(result, tool_context)
        execution_trace = [
            {
                "cycle": 1,
                "state": "PLAN",
                "selected_tools": plan,
            },
            {
                "cycle": 2,
                "state": "READ",
                "completed_tools": list(tool_context),
                "failed_tools": [
                    name
                    for name, value in tool_context.items()
                    if isinstance(value, dict) and value.get("available") is False
                ],
            },
            {
                "cycle": 3,
                "state": "RETRIEVE",
                "source": "local vector knowledge index",
            },
            {
                "cycle": 4,
                "state": "SYNTHESIZE",
                "answer_type": result.get("answer_type"),
            },
        ]
        result.update(
            {
                "assistant_name": "AI Assistant",
                "conversation_id": conversation_id,
                "agentic": True,
                "read_only": True,
                "plan": plan,
                "tool_results": tool_context,
                "tool_schemas": self.registry.schemas(),
                "execution_trace": execution_trace,
            }
        )
        result.setdefault("safety", safety["note"])
        with self._lock:
            conversation.messages.append(
                {"role": "assistant", "content": str(result.get("answer", ""))}
            )
            conversation.messages[:] = conversation.messages[-12:]
        return result

    def reset(self, conversation_id: str) -> bool:
        with self._lock:
            return self._conversations.pop(conversation_id, None) is not None


_assistant = AgenticAssistant()


def get_agentic_assistant() -> AgenticAssistant:
    return _assistant


def _apply_live_evidence(result: dict[str, Any], tool_context: dict[str, Any]) -> None:
    """Turn tool evidence into a deterministic, inspectable live answer."""
    system_health = tool_context.get("read_system_health")
    if (
        isinstance(system_health, dict)
        and system_health.get("read_only") is True
        and isinstance(system_health.get("checks"), list)
    ):
        failed = [
            str(item.get("name"))
            for item in system_health["checks"]
            if isinstance(item, dict) and item.get("status") == "FAIL"
        ]
        warnings = [
            str(item.get("name"))
            for item in system_health["checks"]
            if isinstance(item, dict) and item.get("status") == "WARNING"
        ]
        overall = str(system_health.get("overall") or "UNKNOWN")
        result.update(
            {
                "answer_type": "LIVE_SYSTEM_HEALTH",
                "scope": "Current DairyOS runtime and persisted data integrity",
                "title": "Read-only DairyOS system health",
                "answer": (
                    f"System Health is {overall}. "
                    f"The check recorded {len(failed)} failure(s) and {len(warnings)} warning(s)."
                ),
                "expanded_explanation": (
                    "The report includes database responsiveness, current schema and canonical columns, "
                    "persistence visibility, event/outbox linkage, clinical record links, backup protection, "
                    "managed data layout, AI Assistant knowledge availability and runtime state. "
                    + (
                        "Failures: " + ", ".join(failed) + ". "
                        if failed
                        else ""
                    )
                    + ("Warnings: " + ", ".join(warnings) + "." if warnings else "")
                ),
                "effects": ["Only diagnostic evidence was read; no system or farm record was changed."],
                "safety": system_health.get(
                    "safety",
                    "System health is diagnostic and read-only; it does not repair or reset DairyOS.",
                ),
            }
        )
        return

    cop = tool_context.get("read_cop_metrics")
    if isinstance(cop, dict) and cop.get("status"):
        period = cop.get("period") or {}
        label = f"{period.get('effective_start')} to {period.get('effective_end')}"
        if cop.get("status") == "OK":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS COP authority",
                    "title": "COP/L from persisted DairyOS data",
                    "answer": (
                        f"For the completed period {label}, the governed period COP/L is "
                        f"{cop.get('period_cop_per_litre')}. The average daily COP/L is "
                        f"{cop.get('average_daily_cop_per_litre')}, and the maximum daily COP/L is "
                        f"{cop.get('maximum_daily_cop_per_litre')}."
                    ),
                    "expanded_explanation": (
                        f"This uses {cop.get('valid_daily_days')} complete daily authority rows and "
                        f"{cop.get('period_milk_litres')} litres of persisted milk. "
                        "The period figure is weighted by milk volume; average and maximum are daily statistics. "
                        f"{cop.get('calculation_basis')}."
                    ),
                    "preconditions": [
                        "The requested dates are limited to completed operational days."
                    ],
                    "steps": [
                        "Read the governed TMR snapshots, attributed Finance OPEX and milk ledger.",
                        "Recompute the period and daily statistics from those persisted authorities.",
                    ],
                    "expected_result": "A traceable COP/L answer with its period, daily coverage and data basis.",
                    "next_actions": [
                        "Ask for a different month, date range or daily COP/L breakdown."
                    ],
                    "effects": [
                        "No operational record was changed; only persisted authorities were read."
                    ],
                }
            )
        else:
            missing = ", ".join(cop.get("missing_authority_days") or []) or "none"
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA_INCOMPLETE",
                    "scope": "Persisted DairyOS COP authority",
                    "title": "COP/L authority is incomplete",
                    "answer": (
                        f"I cannot provide a defensible COP/L for {label}. The persisted cost authority is "
                        f"{cop.get('status')}; missing authority days: {missing}. I did not substitute zero."
                    ),
                    "expanded_explanation": (
                        "DairyOS keeps missing historical TMR authority unavailable rather than converting it to a zero cost. "
                        "The response remains read-only and identifies the exact days that prevent a complete calculation."
                    ),
                    "effects": [
                        "Incomplete COP/L is surfaced as unavailable instead of being miscalculated."
                    ],
                }
            )
        result["safety"] = (
            "Live operational values were read without writes. Missing or incomplete authority is never represented as zero."
        )
        return

    health = tool_context.get("read_health_insight")
    if isinstance(health, dict) and health.get("metric") == "health_insight":
        candidates = health.get("probable_conditions") or []
        if health.get("history_requested"):
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS health history",
                    "title": "Health history from persisted records",
                    "answer": (
                        f"The selected period contains {health.get('health_case_count', 0)} persisted health case(s), "
                        f"{health.get('matching_observation_count', 0)} health observation(s), and "
                        f"{health.get('treatment_count', 0)} treatment record(s)."
                    ),
                    "expanded_explanation": (
                        "Health cases, observations and treatments are reported as separate persisted authorities. "
                        "A health case is not inferred from an observation, and a treatment is not treated as a confirmed diagnosis. "
                        "Bounded records and the selected period are available in the read-only evidence."
                    ),
                    "effects": ["No health, treatment or case record was changed."],
                    "safety": health.get("assessment_boundary"),
                }
            )
            return
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
            result.update(
                {
                    "answer_type": "LIVE_HEALTH_INSIGHT",
                    "scope": "Persisted health evidence and vetted veterinary reference",
                    "title": "Probable health conditions to assess",
                    "answer": (
                        f"The entered signs are compatible with these possible conditions: {names}. "
                        "They are differentials for veterinary assessment, not a confirmed diagnosis. "
                        f"Initial treatment/management guidance: {management or 'seek veterinary assessment promptly.'}"
                    ),
                    "expanded_explanation": (
                        f"The Assistant found {health.get('matching_observation_count', 0)} matching persisted health observations "
                        f"and {health.get('treatment_count', 0)} persisted treatments. "
                        f"Diagnostic path: {diagnostic or 'veterinarian-directed examination and testing.'} "
                        f"Urgent signs to escalate: {urgent or 'any systemic deterioration.'} "
                        "Review the candidate evidence, then have the responsible veterinarian examine the animal and record the authorised plan."
                    ),
                    "preconditions": [
                        "Protect animal welfare and capture objective signs, timing and animal identity."
                    ],
                    "steps": [
                        "Review the probable-condition cards and urgent signs.",
                        "Obtain veterinarian-directed examination/testing.",
                        "Record the confirmed diagnosis, authorised treatment, dose and withdrawal period in DairyOS.",
                    ],
                    "expected_result": "A safe differential assessment with traceable clinical evidence and professional escalation.",
                    "next_actions": [
                        "Escalate urgent or systemic deterioration immediately.",
                        "Ask for one animal ID to narrow the persisted health evidence.",
                    ],
                    "effects": [
                        "Only read-only health and reference evidence was used; no treatment was prescribed or recorded."
                    ],
                    "safety": health.get("assessment_boundary"),
                }
            )
        else:
            result.update(
                {
                    "answer_type": "HEALTH_REFERENCE_NO_MATCH",
                    "scope": "Persisted health evidence and vetted veterinary reference",
                    "title": "No sufficiently grounded health differential",
                    "answer": "I could not match the entered signs to a sufficiently grounded disease-reference candidate.",
                    "expanded_explanation": "Record objective observations and seek veterinarian-directed examination; the Assistant will not invent a diagnosis or prescribe treatment.",
                    "safety": health.get("assessment_boundary"),
                }
            )
        return

    schema = tool_context.get("read_database_schema")
    if (
        isinstance(schema, dict)
        and schema.get("metric") == "database_schema"
        and schema.get("read_only") is True
    ):
        tables = schema.get("tables") or []
        selected = schema.get("selected_table")
        if isinstance(selected, dict):
            table_name = selected.get("table") or "the selected table"
            columns = selected.get("columns") or []
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA_SCHEMA",
                    "scope": "Current DairyOS application database schema",
                    "title": f"{table_name} schema from persisted database",
                    "answer": (
                        f"The current {table_name} table has {len(columns)} column(s) and "
                        f"{selected.get('row_count', 0)} persisted row(s). Its bounded read-only rows "
                        "and column definitions are included in the evidence."
                    ),
                    "expanded_explanation": (
                        "The schema was inspected from the current DairyOS database without changing any row, "
                        "index or definition. Credential-like values are omitted or redacted."
                    ),
                }
            )
        else:
            table_names = [
                str(item.get("table"))
                for item in tables
                if isinstance(item, dict) and item.get("table")
            ]
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA_SCHEMA",
                    "scope": "Current DairyOS application database schema",
                    "title": "Current DairyOS database schema",
                    "answer": (
                        f"The current DairyOS database contains {schema.get('table_count', len(tables))} "
                        f"table(s): {', '.join(table_names) or 'none'}. Full column definitions, row counts "
                        "and any bounded selected rows are included in the read-only evidence."
                    ),
                    "expanded_explanation": (
                        "The schema catalog was read from the current application database. No database row or "
                        "definition was changed, and credential-like values are omitted or redacted."
                    ),
                }
            )
        result.update(
            {
                "effects": ["No database table row, schema definition or credential was changed."],
                "safety": "The current DairyOS database schema was inspected through a transaction-scoped read-only guard.",
            }
        )
        return

    data = tool_context.get("read_operational_data")
    if isinstance(data, dict) and isinstance(data.get("evidence"), dict):
        evidence = data["evidence"]
        metric = evidence.get("metric")
        if metric == "operational_multi_domain":
            summaries = []
            for item in evidence.get("evidence") or []:
                item_metric = item.get("metric")
                if item_metric == "reproduction_and_calf_lifecycle":
                    summaries.append(
                        f"{item.get('actual_calving_events')} calving event(s) and {item.get('calf_animal_records')} calf record(s)"
                    )
                elif item_metric == "mortality":
                    summaries.append(
                        f"{item.get('mortality_events')} mortality event(s)"
                    )
                elif item_metric == "milk_production":
                    summaries.append(
                        f"{item.get('total_litres')} litres of milk production"
                    )
                elif item_metric == "milk_dispositions":
                    summaries.append(
                        f"{item.get('quantity_litres')} litres across {item.get('record_count')} milk dispositions"
                    )
                else:
                    summaries.append(
                        f"{item.get('record_count', 0)} {item_metric or 'operational'} record(s)"
                    )
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Multiple persisted DairyOS operational authorities",
                    "title": "Combined operational answer from persisted data",
                    "answer": "The selected period contains "
                    + "; ".join(summaries)
                    + ".",
                    "expanded_explanation": "Each requested domain was read from its own persisted authority and kept distinct in the supporting evidence; no record was changed or silently omitted.",
                    "effects": ["No operational record was changed."],
                    "safety": "Multiple operational authorities were read without writes.",
                }
            )
        elif metric == "operational_period_empty":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA_UNAVAILABLE",
                    "scope": "Requested DairyOS operational period",
                    "title": "No completed operational date in the requested period",
                    "answer": "The requested date range contains no completed operational day, so no live value was substituted.",
                    "expanded_explanation": "DairyOS does not turn an empty or future period into a fabricated zero. Ask for a completed operational date or another period.",
                    "effects": ["No operational record was changed."],
                    "safety": "No live value was available for the requested period; no zero was invented.",
                }
            )
        elif metric == "milk_production":
            milk_answer = (
                f"Persisted DairyOS milk production for the requested period is {evidence.get('total_litres')} litres across {evidence.get('days_with_production')} production days."
                if evidence.get("record_count") or evidence.get("missing_yield_records")
                else "No persisted milk production records were found for the requested period."
            )
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS milk production ledger",
                    "title": "Milk production from persisted records",
                    "answer": milk_answer,
                    "expanded_explanation": "VOID and NOT_MILKED session statements were excluded, and entered session yields were summed according to the milk authority. The daily breakdown is included in the read-only tool result.",
                    "effects": [
                        "No milk record was changed; the answer reads the authoritative milk ledger."
                    ],
                    "safety": "Live operational data was read without writes.",
                }
            )
        elif metric == "reproduction_and_calf_lifecycle":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS reproduction and animal records",
                    "title": "Calving and calf records from persisted data",
                    "answer": f"The selected period contains {evidence.get('actual_calving_events')} actual persisted calving event(s) and {evidence.get('calf_animal_records')} calf animal record(s).",
                    "expanded_explanation": "Actual calving events are classified from persisted breeding records; calf master records are reported separately because a birth event and an animal registration are different authorities.",
                    "effects": ["No reproductive or animal record was changed."],
                    "safety": "Live operational data was read without writes.",
                }
            )
        elif metric == "mortality":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS mortality authority",
                    "title": "Mortality from persisted records",
                    "answer": f"The selected period contains {evidence.get('mortality_events')} persisted mortality event(s). The current animal master contains {evidence.get('currently_deceased_animals')} deceased animal record(s).",
                    "expanded_explanation": "Mortality events are read from durable animal-disposition events; current deceased master records are shown separately so historical event counts are not confused with current state.",
                    "effects": ["No lifecycle or mortality record was changed."],
                    "safety": "Live operational data was read without writes.",
                }
            )
        elif metric == "finance_transactions":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS Finance records",
                    "title": "Finance records from persisted data",
                    "answer": f"The selected period contains {evidence.get('transaction_count')} Finance transaction(s): income {evidence.get('income_total')} and expenses {evidence.get('expense_total')}, for net cash flow {evidence.get('net_cash_flow')}.",
                    "expanded_explanation": "The answer reads persisted financial transactions and preserves their status and COP metadata in the supporting evidence. VOID and other inactive records are excluded from totals by the Finance classifier.",
                    "effects": ["No financial transaction was changed."],
                    "safety": "Finance data was read without writes; the Assistant cannot approve or post a transaction.",
                }
            )
        elif metric == "feed_records":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS feed records",
                    "title": "Feed records from persisted data",
                    "answer": f"The selected period contains {evidence.get('feed_record_count')} feed record(s), totalling {evidence.get('quantity_kg')} kg and recorded feed cost {evidence.get('recorded_feed_cost')}.",
                    "expanded_explanation": "This is the feed-record ledger. Governed historical COP uses immutable daily TMR cost snapshots, which are kept distinct from feeding events in the evidence response.",
                    "effects": ["No feed or TMR record was changed."],
                    "safety": "Feed data was read without writes.",
                }
            )
        elif metric == "animal_register":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS animal register",
                    "title": "Animal records from persisted data",
                    "answer": f"The selected scope contains {evidence.get('animal_count')} persisted animal record(s).",
                    "expanded_explanation": "The response includes lifecycle and status counts plus bounded animal records. Permanent animal identity and historical records remain intact; the read-only Assistant never deletes or changes an animal.",
                    "effects": ["No animal or lifecycle record was changed."],
                    "safety": "Animal data was read without writes.",
                }
            )
        elif metric == "milk_dispositions":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS milk disposition and sale records",
                    "title": "Milk destinations from persisted data",
                    "answer": (
                        f"The selected period contains {evidence.get('record_count')} active milk disposition record(s) "
                        f"covering {evidence.get('quantity_litres')} litres. "
                        f"Recorded amount due is {evidence.get('amount_due')}, with {evidence.get('amount_received')} received."
                    ),
                    "expanded_explanation": "Disposition types and bounded sale/wastage records are included as supporting evidence. VOID rows are excluded from the totals.",
                    "effects": [
                        "No milk destination, sale or receipt record was changed."
                    ],
                    "safety": "Milk disposition and sale data was read without writes.",
                }
            )
        elif metric == "operational_input_events":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS operational input events",
                    "title": "Operational input history from persisted events",
                    "answer": (
                        f"The selected period contains {evidence.get('record_count')} persisted "
                        f"{evidence.get('input_type')} input event(s)."
                    ),
                    "expanded_explanation": "The event journal is the durable audit authority for this input type; VOID inputs are excluded and bounded payloads are redacted before display.",
                    "effects": ["No operational input event was changed."],
                    "safety": "Operational input history was read without writes.",
                }
            )
        elif metric == "operational_table":
            table_name = (evidence.get("table") or {}).get("table", "selected table")
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS database table",
                    "title": f"{table_name} records from persisted data",
                    "answer": f"The selected scope contains {evidence.get('record_count')} persisted record(s) in {table_name}.",
                    "expanded_explanation": "The response contains bounded, sanitised rows and states whether a date column was used for the requested period. The database transaction was read-only.",
                    "effects": ["No database table row was changed."],
                    "safety": "The selected table was read without writes; credential-like columns are redacted.",
                }
            )
        elif metric == "operational_tables":
            table_names = [
                str((item.get("table") or {}).get("table"))
                for item in evidence.get("tables") or []
            ]
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA",
                    "scope": "Persisted DairyOS database tables",
                    "title": "Selected operational tables from persisted data",
                    "answer": (
                        f"I read {evidence.get('record_count')} persisted record(s) across "
                        f"{', '.join(table_names)} in read-only mode."
                    ),
                    "expanded_explanation": "Each table includes a bounded, sanitised record sample and its selected-period count where a date column is available.",
                    "effects": ["No operational table row was changed."],
                    "safety": "The selected operational tables were read without writes; credential-like values are redacted.",
                }
            )
        elif metric == "operational_data_catalog":
            result.update(
                {
                    "answer_type": "LIVE_OPERATIONAL_DATA_CATALOG",
                    "scope": "Current DairyOS application database",
                    "title": "Current operational data catalog",
                    "answer": "I read the current DairyOS operational data catalog in read-only mode. The tool result contains counts for the available domain authorities.",
                    "expanded_explanation": "Use a specific area, date, or table name to receive the corresponding bounded records and calculation. The database schema tool can enumerate every current table and its columns without exposing credentials.",
                    "effects": ["No operational data was changed."],
                    "safety": "The operational database was read through a transaction-scoped read-only guard.",
                }
            )

    logs = tool_context.get("read_operational_logs")
    if isinstance(logs, dict) and logs.get("database_logs") is not None:
        journal = logs["database_logs"].get("event_journal") or []
        operational = logs["database_logs"].get("operational_events") or []
        result.update(
            {
                "answer_type": "LIVE_OPERATIONAL_LOGS",
                "scope": "Persisted DairyOS logs and runtime evidence",
                "title": "Operational log evidence",
                "answer": f"I read {len(journal)} persistent journal entries and {len(operational)} operational-event entries, plus bounded local runtime log tails where available.",
                "expanded_explanation": "The log evidence is bounded and sanitised for display. It is read inside the same database read-only transaction; no event, outbox row or file was changed.",
                "effects": ["Only log and audit evidence was read."],
                "safety": "Logs are read-only and credential-like values are redacted.",
            }
        )

    unavailable = [
        name
        for name, value in tool_context.items()
        if isinstance(value, dict) and value.get("available") is False
    ]
    health_unavailable = tool_context.get("read_health_insight")
    if (
        isinstance(health_unavailable, dict)
        and health_unavailable.get("available") is False
        and str(result.get("scope") or "").startswith(
            "Educational health and veterinary information"
        )
    ):
        result.update(
            {
                "answer_type": "HEALTH_REFERENCE_ONLY",
                "title": "Vetted veterinary reference (live records unavailable)",
                "expanded_explanation": (
                    f"The local veterinary reference is available, but persisted health evidence could not be read: "
                    f"{health_unavailable.get('error')}. No live observation, case or treatment value was invented. "
                    "Restore database readiness and retry when animal-specific history is required."
                ),
                "safety": (
                    "This is educational veterinary information only. A veterinarian must examine the animal, "
                    "confirm the condition, choose treatment, dose and withdrawal, and record the authorised plan."
                ),
            }
        )
        return
    successful_live_read = any(
        name != "read_safety_policy"
        and isinstance(value, dict)
        and value.get("read_only") is True
        for name, value in tool_context.items()
    )
    if unavailable and not successful_live_read:
        names = ", ".join(unavailable)
        result.update(
            {
                "answer_type": "LIVE_DATA_UNAVAILABLE",
                "scope": "Current DairyOS operational database or runtime logs",
                "title": "Live DairyOS data could not be read",
                "answer": (
                    f"I could not read the requested live DairyOS evidence because {names} "
                    "was unavailable. I have not invented a value or changed any record."
                ),
                "expanded_explanation": "The grounded knowledge response remains available for procedures, but current operational values must be retried after database or runtime readiness is restored.",
                "effects": ["No operational record was changed."],
                "safety": "Live data is unavailable; no value was substituted or fabricated.",
            }
        )

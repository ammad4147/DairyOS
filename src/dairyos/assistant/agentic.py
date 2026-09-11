"""Bounded Agentic RAG runtime for the DairyOS AI Assistant.

The controller is intentionally local and deterministic.  It plans a bounded
set of read-only authorities, executes them, observes typed evidence, performs
at most one diagnostic iteration when a live authority fails, and synthesizes
one validated :class:`AssistantResponse`.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from fastapi import HTTPException
from pydantic import Field, ValidationError
from sqlalchemy.exc import SQLAlchemyError

from dairyos.assistant.contracts import (
    AgentState,
    AssistantResponse,
    StrictModel,
)
from dairyos.assistant.conversation import ConversationStore
from dairyos.assistant.evidence import (
    ResponseDraft,
    aggregate_knowledge,
    aggregate_live_evidence,
    aggregate_tool_evidence,
    evidence_item,
)
from dairyos.assistant.knowledge import GroundedAssistant
from dairyos.assistant.operational import (
    read_cop_metrics,
    read_health_insight,
    read_operational_data,
    read_operational_logs,
)
from dairyos.assistant.routing import (
    classify_request,
    has_period_reference,
    looks_like_follow_up,
)


class EmptyToolArguments(StrictModel):
    """Closed argument object for tools that take no user parameters."""


class KnowledgeToolArguments(StrictModel):
    question: str = Field(min_length=1, max_length=4_000)
    role: str = Field(default="Operator", max_length=80)


class DateReaderToolArguments(StrictModel):
    question: str = Field(min_length=1, max_length=4_000)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    month: str | int | None = None
    year: str | int | None = None


class OperationalDataToolArguments(DateReaderToolArguments):
    table_name: str | None = Field(default=None, max_length=160)
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=50, ge=1, le=100)
    # Kept as a compatibility alias for callers from earlier builds.  New
    # plans use page/page_size so the response exposes explicit pagination.
    limit: int | None = Field(default=None, ge=1, le=100)


class HealthToolArguments(DateReaderToolArguments):
    animal_id: str | None = Field(default=None, max_length=160)
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=50, ge=1, le=100)


class LogsToolArguments(StrictModel):
    question: str = Field(min_length=1, max_length=4_000)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=50, ge=1, le=100)
    limit: int | None = Field(default=None, ge=1, le=100)


class SchemaToolArguments(StrictModel):
    question: str | None = Field(default=None, max_length=4_000)
    table_name: str | None = Field(default=None, max_length=160)
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=50, ge=1, le=100)
    limit: int | None = Field(default=None, ge=1, le=100)


@dataclass(frozen=True)
class AssistantTool:
    name: str
    description: str
    arguments_model: type[StrictModel]
    handler: Callable[..., dict[str, Any]]

    def schema(self) -> dict[str, Any]:
        parameters = self.arguments_model.model_json_schema()
        parameters.pop("title", None)
        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
        }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        validated = self.arguments_model.model_validate(arguments)
        return self.handler(**validated.model_dump(exclude_none=True))


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


def _read_database_schema(**arguments: Any) -> dict[str, Any]:
    from dairyos.assistant.operational import _read_database_schema as read_schema

    return read_schema(**arguments)


class AssistantToolRegistry:
    """Strict, typed registry for every Assistant tool."""

    def __init__(self) -> None:
        self._tools = {
            "search_knowledge_base": AssistantTool(
                "search_knowledge_base",
                "Retrieve grounded DairyOS procedures and implementation evidence.",
                KnowledgeToolArguments,
                _knowledge,
            ),
            "knowledge_coverage": AssistantTool(
                "knowledge_coverage",
                "Report indexed corpus coverage and validation status.",
                EmptyToolArguments,
                _coverage,
            ),
            "read_safety_policy": AssistantTool(
                "read_safety_policy",
                "Explain the AI Assistant safety boundary.",
                EmptyToolArguments,
                _safety,
            ),
            "read_system_snapshot": AssistantTool(
                "read_system_snapshot",
                "Read DairyOS version and backup protection status.",
                EmptyToolArguments,
                _system_snapshot,
            ),
            "read_system_health": AssistantTool(
                "read_system_health",
                "Run current DairyOS read-only integrity, schema, persistence, backup and Assistant readiness checks.",
                EmptyToolArguments,
                _system_health,
            ),
            "read_command_center": AssistantTool(
                "read_command_center",
                "Read current operational Command Center context without changing decisions.",
                EmptyToolArguments,
                _command_center_snapshot,
            ),
            "read_operational_data": AssistantTool(
                "read_operational_data",
                "Read current persisted DairyOS operational data and canonical domain summaries without writing.",
                OperationalDataToolArguments,
                _read_data,
            ),
            "read_cop_metrics": AssistantTool(
                "read_cop_metrics",
                "Read persisted milk, governed TMR feed cost and attributed Finance OPEX to calculate COP/L statistics.",
                DateReaderToolArguments,
                _read_cop,
            ),
            "read_health_insight": AssistantTool(
                "read_health_insight",
                "Read persisted health evidence and retrieve probable disease differentials from the vetted veterinary corpus.",
                HealthToolArguments,
                _read_health,
            ),
            "read_operational_logs": AssistantTool(
                "read_operational_logs",
                "Read bounded persistent event-journal, operational-event, projection-outbox and local runtime log evidence.",
                LogsToolArguments,
                _read_logs,
            ),
            "read_database_schema": AssistantTool(
                "read_database_schema",
                "Inspect current DairyOS database tables, columns, row counts and bounded rows without changing the database.",
                SchemaToolArguments,
                _read_database_schema,
            ),
        }

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Unknown AI Assistant tool: {name}")
        return tool.execute(arguments)


@dataclass
class Conversation:
    messages: list[dict[str, str]] = field(default_factory=list)


class AgenticAssistant:
    """Run the bounded AI Assistant state machine."""

    MAX_ITERATIONS = 3

    def __init__(self) -> None:
        self.registry = AssistantToolRegistry()
        self.conversation_store = ConversationStore()
        self._conversations: dict[str, Conversation] = {}
        self._lock = RLock()

    def _new_state(
        self,
        question: str,
        role: str,
        conversation_id: str | None,
    ) -> AgentState:
        resolved_id = conversation_id or str(uuid.uuid4())
        persistence = "MEMORY_ONLY"
        with self._lock:
            conversation = self._conversations.get(resolved_id)
            if conversation is None:
                conversation = Conversation()
                try:
                    conversation.messages[:] = self.conversation_store.load(resolved_id)
                    persistence = "PERSISTED"
                except (OSError, RuntimeError, SQLAlchemyError):
                    # Conversation persistence is additive.  A transient
                    # database problem must not prevent a read-only answer.
                    persistence = "MEMORY_ONLY"
                self._conversations[resolved_id] = conversation
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
            history = list(conversation.messages[-12:])
            try:
                self.conversation_store.append(
                    resolved_id,
                    "user",
                    question,
                    perspective=role,
                    metadata={"message_type": "question"},
                )
                persistence = "PERSISTED"
            except (OSError, RuntimeError, SQLAlchemyError):
                persistence = "MEMORY_ONLY"
        state = AgentState(
            conversation_id=resolved_id,
            role=role,
            question=question,
            history=history,
            previous_user_question=previous_user_question,
            max_iterations=self.MAX_ITERATIONS,
            conversation_persistence=persistence,
        )
        # Keep the pre-turn context in the trace input without adding another
        # mutable field to the public state contract.
        state.execution_trace.append(
            {"cycle": 0, "state": "INPUT", "has_previous_context": bool(previous_context.strip())}
        )
        return state

    def _plan(self, state: AgentState) -> None:
        previous_context = "\n".join(
            item["content"] for item in state.history[:-1][-4:]
        )
        classification = classify_request(state.question, previous_context)
        state.route = classification.route
        state.live_data_required = classification.live_data_required
        state.documentation_required = classification.documentation_required
        state.plan = list(classification.tools)
        state.pending_tools = list(classification.tools)
        state.phase = "PLAN"
        state.execution_trace.append(
            {
                "cycle": 1,
                "state": "PLAN",
                "route": classification.route,
                "live_data_required": classification.live_data_required,
                "documentation_required": classification.documentation_required,
                "selected_tools": list(classification.tools),
                "reason": classification.reason,
            }
        )

    def _tool_arguments(self, state: AgentState, tool_name: str) -> dict[str, Any]:
        if tool_name == "search_knowledge_base":
            context = "\n".join(item["content"] for item in state.history[-4:])
            return {"question": context, "role": state.role}
        if tool_name == "read_database_schema":
            return {"question": state.question}
        if tool_name not in {
            "read_operational_data",
            "read_cop_metrics",
            "read_health_insight",
            "read_operational_logs",
        }:
            return {}
        tool_question = state.question
        previous_context = "\n".join(
            item["content"] for item in state.history[:-1][-4:]
        )
        if (
            state.previous_user_question
            and looks_like_follow_up(state.question, previous_context)
            and not has_period_reference(state.question)
        ):
            tool_question = f"{state.previous_user_question}\n{state.question}"
        return {"question": tool_question}

    def _act(self, state: AgentState) -> None:
        state.phase = "ACT"
        pending = list(state.pending_tools)
        state.pending_tools = []
        for tool_name in pending:
            if tool_name in state.completed_tools:
                continue
            try:
                state.tool_results[tool_name] = self.registry.execute(
                    tool_name, self._tool_arguments(state, tool_name)
                )
            except (
                FileNotFoundError,
                OSError,
                RuntimeError,
                SQLAlchemyError,
                TypeError,
                ValueError,
                ValidationError,
                HTTPException,
            ) as exc:
                state.tool_results[tool_name] = {
                    "available": False,
                    "error": str(exc),
                }
                state.failed_tools.append(tool_name)
            state.completed_tools.append(tool_name)
        state.execution_trace.append(
            {
                "cycle": len(state.execution_trace) + 1,
                "state": "ACT",
                "completed_tools": list(state.completed_tools),
                "failed_tools": list(state.failed_tools),
                "read_only": True,
            }
        )
        state.phase = "OBSERVE"

    def _observe(self, state: AgentState) -> None:
        state.phase = "OBSERVE"
        state.evidence = aggregate_tool_evidence(state.tool_results)
        preferred = [
            name
            for name in state.plan
            if name not in {"read_safety_policy", "search_knowledge_base"}
        ]
        if state.live_data_required:
            observation = aggregate_live_evidence(state.tool_results, preferred)
            state.data_quality = observation.data_quality
        else:
            knowledge = state.tool_results.get("search_knowledge_base")
            state.data_quality = (
                aggregate_knowledge(knowledge).data_quality
                if isinstance(knowledge, dict)
                else []
            )
        state.execution_trace.append(
            {
                "cycle": len(state.execution_trace) + 1,
                "state": "OBSERVE",
                "evidence_items": len(state.evidence),
                "failed_tools": list(state.failed_tools),
            }
        )
        retryable_failures = [
            name
            for name in state.failed_tools
            if name not in {"read_operational_logs", "read_safety_policy"}
        ]
        if (
            state.live_data_required
            and retryable_failures
            and "read_operational_logs" not in state.completed_tools
            and state.iteration + 1 < state.max_iterations
        ):
            state.iteration += 1
            state.pending_tools = ["read_operational_logs"]
            state.phase = "ITERATE"
            state.execution_trace.append(
                {
                    "cycle": len(state.execution_trace) + 1,
                    "state": "ITERATE",
                    "reason": "A bounded diagnostic log read was added after a live authority failed.",
                    "selected_tools": ["read_operational_logs"],
                }
            )
        else:
            state.phase = "SYNTHESIZE"

    def _knowledge_draft(self, state: AgentState) -> ResponseDraft:
        value = state.tool_results.get("search_knowledge_base")
        if not isinstance(value, dict):
            value = {"available": False, "error": "No knowledge result was returned."}
        draft = aggregate_knowledge(value)
        if draft.evidence == [] and isinstance(value, dict):
            draft.evidence = [evidence_item("search_knowledge_base", value)]
        return draft

    def _synthesize(self, state: AgentState) -> dict[str, Any]:
        if state.live_data_required:
            preferred = [
                name
                for name in state.plan
                if name not in {"read_safety_policy", "search_knowledge_base"}
            ]
            draft = aggregate_live_evidence(state.tool_results, preferred)
            knowledge = state.tool_results.get("search_knowledge_base")
            if state.documentation_required and isinstance(knowledge, dict):
                draft.source_mode = (
                    "LIVE_UNAVAILABLE"
                    if draft.source_mode == "LIVE_UNAVAILABLE"
                    else "LIVE_PLUS_KNOWLEDGE"
                )
                draft.evidence.append(evidence_item("search_knowledge_base", knowledge))
                if not any(item.source == "knowledge_base" for item in draft.data_quality):
                    draft.data_quality.append(
                        aggregate_knowledge(knowledge).data_quality[0]
                    )
        else:
            draft = self._knowledge_draft(state)
        state.phase = "SYNTHESIZE"
        safety_result = state.tool_results.get("read_safety_policy")
        if isinstance(safety_result, dict):
            safety_note = str(safety_result.get("note") or "")
            if safety_note and not draft.safety:
                draft.safety = safety_note
        state.evidence = draft.evidence
        state.data_quality = draft.data_quality
        state.execution_trace.append(
            {
                "cycle": len(state.execution_trace) + 1,
                "state": "SYNTHESIZE",
                "answer_type": draft.answer_type,
                "source_mode": draft.source_mode,
                "evidence_items": len(draft.evidence),
            }
        )
        agent_state = state.model_dump(
            mode="json",
            exclude={"tool_results", "evidence", "data_quality"},
        )
        response = AssistantResponse(
            conversation_id=state.conversation_id,
            question=state.question,
            role=state.role,
            answer_type=draft.answer_type,
            scope=draft.scope,
            title=draft.title,
            answer=draft.answer or "No grounded answer was produced.",
            expanded_explanation=draft.expanded_explanation,
            source_mode=draft.source_mode,
            conversation_persistence=state.conversation_persistence,
            read_only=True,
            database_read=draft.database_read,
            evidence=draft.evidence,
            data_quality=draft.data_quality,
            next_actions=draft.next_actions,
            safety=draft.safety,
            preconditions=draft.preconditions,
            steps=draft.steps,
            expected_result=draft.expected_result,
            exceptions_recovery=draft.exceptions_recovery,
            effects=draft.effects,
            role_guidance=draft.role_guidance,
            selected_role_guidance=draft.selected_role_guidance,
            sources=draft.sources,
            related=draft.related,
            matched_items=draft.matched_items,
            review=draft.review,
            coverage=draft.coverage,
            plan=state.plan,
            tool_results=state.tool_results,
            tool_schemas=self.registry.schemas(),
            execution_trace=state.execution_trace,
            agent_state=agent_state,
        )
        return response.model_dump(mode="json")

    def ask(
        self,
        question: str,
        role: str = "Operator",
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        state = self._new_state(question, role, conversation_id)
        self._plan(state)
        while state.phase != "SYNTHESIZE":
            if state.phase == "PLAN":
                state.phase = "ACT"
            elif state.phase == "ACT":
                self._act(state)
            elif state.phase == "OBSERVE":
                self._observe(state)
            elif state.phase == "ITERATE":
                state.phase = "ACT"
            else:  # defensive closure for the strict state contract
                state.phase = "SYNTHESIZE"
        result = self._synthesize(state)
        with self._lock:
            conversation = self._conversations.setdefault(
                state.conversation_id, Conversation()
            )
            conversation.messages.append(
                {"role": "assistant", "content": str(result.get("answer", ""))}
            )
            conversation.messages[:] = conversation.messages[-12:]
            try:
                self.conversation_store.append(
                    state.conversation_id,
                    "assistant",
                    str(result.get("answer", "")),
                    perspective=state.role,
                    metadata={
                        "message_type": "answer",
                        "answer_type": result.get("answer_type"),
                        "source_mode": result.get("source_mode"),
                    },
                )
            except (OSError, RuntimeError, SQLAlchemyError):
                result["conversation_persistence"] = "MEMORY_ONLY"
        return result

    def reset(self, conversation_id: str) -> bool:
        with self._lock:
            memory_deleted = self._conversations.pop(conversation_id, None) is not None
            try:
                persisted_deleted = self.conversation_store.delete(conversation_id)
            except (OSError, RuntimeError, SQLAlchemyError):
                persisted_deleted = False
            return memory_deleted or persisted_deleted


_assistant = AgenticAssistant()


def get_agentic_assistant() -> AgenticAssistant:
    return _assistant


def _apply_live_evidence(result: dict[str, Any], tool_context: dict[str, Any]) -> None:
    """Compatibility adapter for older callers; aggregation is now typed."""

    draft = aggregate_live_evidence(tool_context)
    result.update(
        {
            "answer_type": draft.answer_type,
            "scope": draft.scope,
            "title": draft.title,
            "answer": draft.answer,
            "expanded_explanation": draft.expanded_explanation,
            "preconditions": draft.preconditions,
            "steps": draft.steps,
            "expected_result": draft.expected_result,
            "next_actions": [item.description for item in draft.next_actions],
            "exceptions_recovery": draft.exceptions_recovery,
            "effects": draft.effects,
            "safety": draft.safety,
            "evidence": [item.model_dump(mode="json") for item in draft.evidence],
            "data_quality": [item.model_dump(mode="json") for item in draft.data_quality],
        }
    )

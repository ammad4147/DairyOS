"""Local, safe Agentic RAG runtime for the DairyOS AI Assistant."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from dairyos.assistant.knowledge import GroundedAssistant


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


def _command_center_snapshot() -> dict[str, Any]:
    from dairyos.api.dependencies import get_container

    container = get_container()
    return {
        "operational_command_center": container.operational_command_center_service.snapshot(),
        "read_only": True,
    }


class AssistantToolRegistry:
    def __init__(self) -> None:
        obj = {"type": "object", "properties": {}}
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
            "read_command_center": AssistantTool(
                "read_command_center",
                "Read current operational Command Center context without changing decisions.",
                obj,
                _command_center_snapshot,
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
            conversation.messages.append({"role": "user", "content": question})
            context = "\n".join(item["content"] for item in conversation.messages[-4:])
        lowered = context.lower()
        plan = ["read_safety_policy", "search_knowledge_base"]
        if any(
            term in lowered
            for term in ("health", "ready", "backup", "version", "system")
        ):
            plan.insert(1, "read_system_snapshot")
        if any(
            term in lowered
            for term in ("command center", "alert", "decision", "action", "watchlist")
        ):
            plan.insert(1, "read_command_center")
        safety = self.registry.execute(plan[0], {})
        tool_context: dict[str, Any] = {}
        for tool_name in plan[1:]:
            if tool_name == "search_knowledge_base":
                continue
            try:
                tool_context[tool_name] = self.registry.execute(tool_name, {})
            except (
                FileNotFoundError,
                OSError,
                RuntimeError,
                SQLAlchemyError,
                ValueError,
            ) as exc:  # graceful fallback keeps grounded answer available
                tool_context[tool_name] = {"available": False, "error": str(exc)}
        grounded = self.registry.execute(
            "search_knowledge_base", {"question": context, "role": role}
        )
        result = dict(grounded)
        result.update(
            {
                "assistant_name": "AI Assistant",
                "conversation_id": conversation_id,
                "agentic": True,
                "plan": plan,
                "tool_results": tool_context,
                "tool_schemas": self.registry.schemas(),
                "safety": safety["note"],
            }
        )
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

"""Strict contracts for the DairyOS AI Assistant runtime.

The assistant is deliberately modelled as a read-only evidence pipeline.  The
contracts in this module are the boundary between planning, tool execution,
evidence observation and the HTTP response.  Keeping this boundary explicit
prevents a tool result or a knowledge record from silently changing the shape
of an answer.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AgentPhase = Literal["PLAN", "ACT", "OBSERVE", "ITERATE", "SYNTHESIZE"]
SourceMode = Literal[
    "LIVE_ONLY",
    "LIVE_PLUS_KNOWLEDGE",
    "KNOWLEDGE_ONLY",
    "LIVE_UNAVAILABLE",
]
ConversationPersistence = Literal["PERSISTED", "MEMORY_ONLY"]
EvidenceStatus = Literal[
    "AVAILABLE",
    "PARTIAL",
    "UNAVAILABLE",
    "REFERENCE_ONLY",
]
DataQualityStatus = Literal[
    "VERIFIED",
    "PARTIAL",
    "UNAVAILABLE",
    "REFERENCE_ONLY",
    "NOT_APPLICABLE",
]
NextActionKind = Literal[
    "review_evidence",
    "retry_live_data",
    "ask_follow_up",
    "contact_veterinarian",
    "navigate_section",
    "none",
]


class StrictModel(BaseModel):
    """Pydantic base with an explicit, closed response shape."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class EvidenceItem(StrictModel):
    """One inspectable source item used to support an answer."""

    id: str = Field(min_length=1, max_length=160)
    source: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1, max_length=2_000)
    status: EvidenceStatus = "AVAILABLE"
    data_quality_status: DataQualityStatus = "VERIFIED"
    read_only: bool = True
    database_read: bool = False
    source_tables: list[str] = Field(default_factory=list)
    period: dict[str, Any] | None = None
    record_count: int | None = Field(default=None, ge=0)
    pagination: dict[str, Any] | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class DataQualityItem(StrictModel):
    """A concise, user-visible statement about evidence quality."""

    source: str = Field(min_length=1, max_length=80)
    status: DataQualityStatus
    message: str = Field(min_length=1, max_length=1_000)


class NextAction(StrictModel):
    """A safe, bounded follow-up the operator may choose."""

    kind: NextActionKind
    label: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1_000)
    read_only: bool = True
    target: str | None = Field(default=None, max_length=160)


class AgentState(StrictModel):
    """State carried through the bounded PLAN -> ACT -> OBSERVE loop."""

    conversation_id: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=2, max_length=4_000)
    history: list[dict[str, str]] = Field(default_factory=list)
    previous_user_question: str = ""
    route: str = "knowledge"
    live_data_required: bool = False
    documentation_required: bool = False
    phase: AgentPhase = "PLAN"
    iteration: int = Field(default=0, ge=0, le=3)
    max_iterations: int = Field(default=3, ge=1, le=3)
    plan: list[str] = Field(default_factory=list)
    pending_tools: list[str] = Field(default_factory=list)
    completed_tools: list[str] = Field(default_factory=list)
    failed_tools: list[str] = Field(default_factory=list)
    tool_results: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data_quality: list[DataQualityItem] = Field(default_factory=list)
    execution_trace: list[dict[str, Any]] = Field(default_factory=list)
    conversation_persistence: ConversationPersistence = "MEMORY_ONLY"


class AssistantResponse(StrictModel):
    """Stable HTTP response contract for the DairyOS AI Assistant."""

    assistant_name: Literal["AI Assistant"] = "AI Assistant"
    agentic: Literal[True] = True
    conversation_id: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=2, max_length=4_000)
    role: str = Field(min_length=1, max_length=80)
    answer_type: str = Field(min_length=1, max_length=120)
    scope: str = Field(min_length=1, max_length=240)
    title: str = Field(min_length=1, max_length=240)
    answer: str = Field(min_length=1, max_length=8_000)
    expanded_explanation: str = Field(default="", max_length=12_000)
    source_mode: SourceMode = "KNOWLEDGE_ONLY"
    conversation_persistence: ConversationPersistence = "MEMORY_ONLY"
    read_only: bool = True
    database_read: bool = False
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data_quality: list[DataQualityItem] = Field(default_factory=list)
    next_actions: list[NextAction] = Field(default_factory=list)
    safety: str = Field(default="", max_length=4_000)

    # Existing SOP-oriented fields remain part of the stable response because
    # they are useful for guidance answers and are already consumed by the UI.
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected_result: str = ""
    exceptions_recovery: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    role_guidance: dict[str, str] = Field(default_factory=dict)
    selected_role_guidance: str = ""
    sources: list[str] = Field(default_factory=list)
    related: list[dict[str, Any]] = Field(default_factory=list)
    matched_items: list[dict[str, Any]] = Field(default_factory=list)
    review: dict[str, Any] | None = None
    coverage: dict[str, Any] | None = None

    # The raw, bounded tool results are retained for auditability.  They are
    # never writable tools and are rendered behind an explicit evidence panel.
    plan: list[str] = Field(default_factory=list)
    tool_results: dict[str, Any] = Field(default_factory=dict)
    tool_schemas: list[dict[str, Any]] = Field(default_factory=list)
    execution_trace: list[dict[str, Any]] = Field(default_factory=list)
    agent_state: dict[str, Any] = Field(default_factory=dict)

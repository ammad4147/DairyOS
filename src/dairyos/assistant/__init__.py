"""Grounded, read-only AI Assistant services."""

from dairyos.assistant.knowledge import (
    GroundedAssistant,
    LocalVectorIndex,
    knowledge_coverage,
)

__all__ = ["GroundedAssistant", "LocalVectorIndex", "knowledge_coverage"]

from dataclasses import dataclass, field
from datetime import datetime

from .knowledge_pattern import KnowledgePattern


@dataclass
class OperationalMemory:
    """
    Stores operational knowledge for future use.
    """

    memory_id: str
    pattern: KnowledgePattern
    created_at: datetime = field(
        default_factory=datetime.now
    )


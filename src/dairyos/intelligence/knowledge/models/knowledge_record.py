from dataclasses import dataclass


@dataclass
class KnowledgeRecord:
    """
    Represents stored enterprise knowledge.
    """

    knowledge_type: str

    content: str

    source: str

    confidence: float

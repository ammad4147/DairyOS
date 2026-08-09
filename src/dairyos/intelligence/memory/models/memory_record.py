from dataclasses import dataclass


@dataclass
class MemoryRecord:
    """
    Represents an intelligence memory record.

    Future extensions:

    - embeddings
    - vector retrieval
    - relevance scoring
    - lifecycle management
    """


    memory_id: str

    memory_type: str

    content: str

    source: str

    confidence: float

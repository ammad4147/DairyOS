from dataclasses import dataclass



@dataclass
class KnowledgeEntry:


    knowledge_id: str

    category: str

    observation: str

    source: str

    confidence: int

    usage: str

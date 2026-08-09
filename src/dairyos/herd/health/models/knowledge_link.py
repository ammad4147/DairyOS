from dataclasses import dataclass


@dataclass
class KnowledgeLink:

    indicator: str

    possible_conditions: list

    checks: list

    confidence: str

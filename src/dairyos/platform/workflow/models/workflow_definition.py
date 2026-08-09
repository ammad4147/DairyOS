from dataclasses import dataclass, field
from typing import List


@dataclass
class WorkflowDefinition:

    name: str
    description: str = ""

    owner: str = ""

    steps: List[str] = field(default_factory=list)

    trigger_source: str = ""

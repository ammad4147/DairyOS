from dataclasses import dataclass, field


@dataclass
class WorkflowDefinition:

    name: str
    description: str = ""

    owner: str = ""

    steps: list[str] = field(default_factory=list)

    trigger_source: str = ""

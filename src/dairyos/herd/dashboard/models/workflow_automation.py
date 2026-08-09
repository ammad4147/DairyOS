from dataclasses import dataclass, field



@dataclass
class WorkflowAutomation:


    trigger: str

    workflow_name: str

    steps: list = field(default_factory=list)

    priority: str = "MEDIUM"

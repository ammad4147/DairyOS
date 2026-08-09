from dataclasses import dataclass, field



@dataclass
class OperationalWorkflow:


    name: str

    steps: list = field(default_factory=list)

    status: str = "PENDING"

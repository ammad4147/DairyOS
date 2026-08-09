from dataclasses import dataclass


@dataclass
class Workflow:
    """
    Represents an enterprise workflow.

    Future extensions:

    - workflow versioning
    - approval workflow
    - execution metrics
    - ownership
    """


    workflow_type: str

    description: str

    status: str

    initiated_by: str

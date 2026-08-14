from dataclasses import dataclass, field
from datetime import datetime
from dairyos.core.time_utils import utcnow


@dataclass
class WorkflowContext:
    """
    Represents workflow execution context.

    Future extensions:

    - correlation IDs
    - metadata
    - distributed tracing
    """


    workflow_type: str

    initiated_by: str

    created_at: datetime = field(
        default_factory=utcnow
    )

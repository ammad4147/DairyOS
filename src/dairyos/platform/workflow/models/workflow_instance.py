from dataclasses import dataclass
from datetime import datetime, timezone

from dairyos.platform.workflow.models.workflow_status import WorkflowStatus
from dairyos.platform.workflow.models.workflow_definition import WorkflowDefinition


@dataclass
class WorkflowInstance:

    workflow: WorkflowDefinition

    status: WorkflowStatus = WorkflowStatus.CREATED

    current_step: str = ""

    started_at: datetime = datetime.now(timezone.utc)

    completed_at: datetime | None = None

    result: str = ""

from dataclasses import dataclass
from datetime import UTC, datetime

from dairyos.platform.workflow.models.workflow_definition import WorkflowDefinition
from dairyos.platform.workflow.models.workflow_status import WorkflowStatus


@dataclass
class WorkflowInstance:

    workflow: WorkflowDefinition

    status: WorkflowStatus = WorkflowStatus.CREATED

    current_step: str = ""

    started_at: datetime = datetime.now(UTC)

    completed_at: datetime | None = None

    result: str = ""

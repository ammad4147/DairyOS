from dataclasses import dataclass
from datetime import UTC, datetime

from dairyos.platform.scheduler.models.schedule_status import ScheduleStatus


@dataclass
class ScheduledTask:

    name: str

    description: str = ""

    owner: str = ""

    workflow: str = ""

    recurrence: str = ""

    execution_time: datetime = datetime.now(UTC)

    status: ScheduleStatus = ScheduleStatus.CREATED

from dataclasses import dataclass
from datetime import datetime, timezone

from dairyos.platform.scheduler.models.schedule_status import ScheduleStatus


@dataclass
class ScheduledTask:

    name: str

    description: str = ""

    owner: str = ""

    workflow: str = ""

    recurrence: str = ""

    execution_time: datetime = datetime.now(timezone.utc)

    status: ScheduleStatus = ScheduleStatus.CREATED

from dairyos.platform.scheduler.models.scheduled_task import ScheduledTask
from dairyos.platform.scheduler.models.schedule_status import ScheduleStatus


class SchedulerService:

    def __init__(self):

        self.tasks = []


    def register(self, task: ScheduledTask):

        task.status = ScheduleStatus.CREATED

        self.tasks.append(task)

        return task


    def activate(self, task: ScheduledTask):

        task.status = ScheduleStatus.ACTIVE

        return task


    def pause(self, task: ScheduledTask):

        task.status = ScheduleStatus.PAUSED

        return task


    def complete(self, task: ScheduledTask):

        task.status = ScheduleStatus.COMPLETED

        return task


    def fail(self, task: ScheduledTask):

        task.status = ScheduleStatus.FAILED

        return task


    def list_tasks(self):

        return self.tasks

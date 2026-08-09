from dairyos.platform.recommendation_workflow.models.recommendation_task import (
    RecommendationTask,
)



class RecommendationWorkflow:
    """
    Converts intelligence recommendations
    into operational workflows.
    """



    def __init__(self):

        self.tasks = []



    def create_task(
        self,
        recommendation_id,
        title,
        assigned_to,
    ):


        task = RecommendationTask(

            recommendation_id=recommendation_id,

            title=title,

            assigned_to=assigned_to,

            status="created",

        )


        self.tasks.append(task)


        return task



    def complete(
        self,
        task_id,
    ):


        for task in self.tasks:

            if id(task) == task_id:

                task.status = "completed"

                return task


        return None


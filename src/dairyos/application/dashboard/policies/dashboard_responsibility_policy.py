from dairyos.application.dashboard.models.dashboard_action import (
    DashboardAction,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)


class DashboardResponsibilityPolicy:
    """
    Resolves operational responsibilities
    displayed to farm users.

    This policy defines what work
    should appear on a user's dashboard.

    It does not execute tasks.
    """


    def actions_for(
        self,
        role: UserRole,
    ) -> list[DashboardAction]:


        if role == UserRole.OWNER:

            return [

                DashboardAction(
                    title="Review farm performance",
                    action_type="review",
                    priority="normal",
                    responsible_role=role.value,
                ),

                DashboardAction(
                    title="Review operational alerts",
                    action_type="alert_review",
                    priority="high",
                    responsible_role=role.value,
                ),
            ]



        if role == UserRole.FARM_MANAGER:

            return [

                DashboardAction(
                    title="Review daily operations",
                    action_type="operations_review",
                    priority="high",
                    responsible_role=role.value,
                ),

                DashboardAction(
                    title="Resolve pending farm tasks",
                    action_type="task_management",
                    priority="high",
                    responsible_role=role.value,
                ),
            ]



        if role == UserRole.MILKING_OPERATOR:

            return [

                DashboardAction(
                    title="Complete milking entries",
                    action_type="milk_recording",
                    priority="critical",
                    responsible_role=role.value,
                ),

                DashboardAction(
                    title="Review milking tasks",
                    action_type="task_review",
                    priority="high",
                    responsible_role=role.value,
                ),
            ]



        if role == UserRole.FEED_SUPERVISOR:

            return [

                DashboardAction(
                    title="Record feeding activities",
                    action_type="feed_recording",
                    priority="critical",
                    responsible_role=role.value,
                ),

                DashboardAction(
                    title="Review feed tasks",
                    action_type="task_review",
                    priority="high",
                    responsible_role=role.value,
                ),
            ]



        if role == UserRole.VETERINARIAN:

            return [

                DashboardAction(
                    title="Review animal health status",
                    action_type="health_review",
                    priority="high",
                    responsible_role=role.value,
                ),

                DashboardAction(
                    title="Record health events",
                    action_type="health_recording",
                    priority="high",
                    responsible_role=role.value,
                ),
            ]



        if role == UserRole.ACCOUNTANT:

            return [

                DashboardAction(
                    title="Review financial position",
                    action_type="financial_review",
                    priority="normal",
                    responsible_role=role.value,
                ),
            ]



        return [

            DashboardAction(
                title="Review assigned tasks",
                action_type="task_review",
                priority="normal",
                responsible_role=role.value,
            ),
        ]

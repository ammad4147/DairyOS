from dairyos.application.dashboard.models.dashboard_role_profile import (
    DashboardRoleProfile,
)

from dairyos.application.dashboard.policies.dashboard_section import (
    DashboardSection,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)


class DashboardRolePolicy:
    """
    Resolves dashboard experience
    based on operational farm role.
    """


    def profile_for(
        self,
        role: UserRole,
    ) -> DashboardRoleProfile:


        if role == UserRole.OWNER:

            return DashboardRoleProfile(

                role_name=role.value,

                sections={
                    DashboardSection.HERD,
                    DashboardSection.PRODUCTION,
                    DashboardSection.FINANCE,
                    DashboardSection.ALERTS,
                    DashboardSection.OPERATIONS,
                },

                priority_metrics=[
                    "daily_milk",
                    "revenue",
                    "feed_cost",
                    "animal_count",
                    "alerts",
                ],
            )


        if role == UserRole.FARM_MANAGER:

            return DashboardRoleProfile(

                role_name=role.value,

                sections={
                    DashboardSection.HERD,
                    DashboardSection.PRODUCTION,
                    DashboardSection.FEED,
                    DashboardSection.HEALTH,
                    DashboardSection.TASKS,
                    DashboardSection.ALERTS,
                    DashboardSection.OPERATIONS,
                },

                priority_metrics=[
                    "milk_production",
                    "pending_tasks",
                    "health_events",
                    "feed_status",
                ],
            )


        if role == UserRole.MILKING_OPERATOR:

            return DashboardRoleProfile(

                role_name=role.value,

                sections={
                    DashboardSection.MILKING,
                    DashboardSection.TASKS,
                    DashboardSection.ALERTS,
                },

                priority_metrics=[
                    "milking_completion",
                    "milk_total",
                    "pending_milking_tasks",
                ],
            )


        if role == UserRole.FEED_SUPERVISOR:

            return DashboardRoleProfile(

                role_name=role.value,

                sections={
                    DashboardSection.FEED,
                    DashboardSection.TASKS,
                    DashboardSection.ALERTS,
                },

                priority_metrics=[
                    "feed_consumption",
                    "feeding_tasks",
                    "feed_exceptions",
                ],
            )


        if role == UserRole.ACCOUNTANT:

            return DashboardRoleProfile(

                role_name=role.value,

                sections={
                    DashboardSection.FINANCE,
                },

                priority_metrics=[
                    "cash_position",
                    "expenses",
                    "revenue",
                ],
            )


        if role == UserRole.VETERINARIAN:

            return DashboardRoleProfile(

                role_name=role.value,

                sections={
                    DashboardSection.HEALTH,
                    DashboardSection.HERD,
                    DashboardSection.ALERTS,
                },

                priority_metrics=[
                    "health_events",
                    "sick_animals",
                    "treatment_status",
                ],
            )


        return DashboardRoleProfile(

            role_name=role.value,

            sections={
                DashboardSection.TASKS,
            },

            priority_metrics=[
                "assigned_tasks",
            ],
        )

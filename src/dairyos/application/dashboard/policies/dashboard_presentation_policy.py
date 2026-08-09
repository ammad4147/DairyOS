from dairyos.application.identity.models.user_role import UserRole

from .dashboard_section import DashboardSection


ROLE_DASHBOARD_SECTIONS = {

    UserRole.OWNER: {
        DashboardSection.HERD,
        DashboardSection.PRODUCTION,
        DashboardSection.FINANCE,
        DashboardSection.ALERTS,
        DashboardSection.OPERATIONS,
    },


    UserRole.FARM_MANAGER: {
        DashboardSection.HERD,
        DashboardSection.PRODUCTION,
        DashboardSection.FEED,
        DashboardSection.HEALTH,
        DashboardSection.MILKING,
        DashboardSection.TASKS,
        DashboardSection.ALERTS,
        DashboardSection.OPERATIONS,
    },


    UserRole.VETERINARIAN: {
        DashboardSection.HERD,
        DashboardSection.HEALTH,
        DashboardSection.ALERTS,
    },


    UserRole.ACCOUNTANT: {
        DashboardSection.FINANCE,
        DashboardSection.ALERTS,
    },


    UserRole.STORE_KEEPER: {
        DashboardSection.FEED,
        DashboardSection.TASKS,
    },


    UserRole.MILKING_OPERATOR: {
        DashboardSection.MILKING,
        DashboardSection.TASKS,
        DashboardSection.ALERTS,
    },


    UserRole.FEED_SUPERVISOR: {
        DashboardSection.FEED,
        DashboardSection.TASKS,
        DashboardSection.ALERTS,
    },


    UserRole.AI_TECHNICIAN: {
        DashboardSection.HERD,
        DashboardSection.HEALTH,
        DashboardSection.TASKS,
    },


    UserRole.LABOURER: {
        DashboardSection.TASKS,
    },

}


class DashboardPresentationPolicy:
    """
    Determines dashboard presentation visibility
    based on operational responsibility.
    """


    def sections_for(
        self,
        role: UserRole,
    ) -> set[DashboardSection]:

        return ROLE_DASHBOARD_SECTIONS.get(
            role,
            set(),
        )

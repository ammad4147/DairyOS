from dairyos.application.identity.models.user_role import UserRole

from dairyos.application.dashboard.policies.dashboard_section import (
    DashboardSection,
)


class DashboardVisibilityPolicy:
    """
    Determines dashboard information visibility
    based on operational responsibility.

    This does not control access.
    Identity permissions control access.

    This controls dashboard presentation scope.
    """


    def can_view_financials(
        self,
        role: UserRole
    ) -> bool:

        return role in {

            UserRole.OWNER,

            UserRole.ACCOUNTANT,

        }



    def can_view_health(
        self,
        role: UserRole
    ) -> bool:

        return role in {

            UserRole.OWNER,

            UserRole.FARM_MANAGER,

            UserRole.VETERINARIAN,

        }



    def can_view_production(
        self,
        role: UserRole
    ) -> bool:

        return role in {

            UserRole.OWNER,

            UserRole.FARM_MANAGER,

            UserRole.MILKING_OPERATOR,

        }



    def can_view_feed(
        self,
        role: UserRole
    ) -> bool:

        return role in {

            UserRole.OWNER,

            UserRole.FARM_MANAGER,

            UserRole.FEED_SUPERVISOR,

            UserRole.STORE_KEEPER,

        }



    def can_view_alerts(
        self,
        role: UserRole
    ) -> bool:

        return role in {

            UserRole.OWNER,

            UserRole.FARM_MANAGER,

            UserRole.VETERINARIAN,

        }



    def sections_for(
        self,
        role: UserRole
    ) -> set[DashboardSection]:

        sections = {

            DashboardSection.OPERATIONS,

            DashboardSection.TASKS,

        }


        if self.can_view_production(role):

            sections.add(
                DashboardSection.PRODUCTION
            )

            sections.add(
                DashboardSection.MILKING
            )



        if self.can_view_feed(role):

            sections.add(
                DashboardSection.FEED
            )



        if self.can_view_health(role):

            sections.add(
                DashboardSection.HEALTH
            )



        if self.can_view_alerts(role):

            sections.add(
                DashboardSection.ALERTS
            )



        if role in {

            UserRole.OWNER,

            UserRole.FARM_MANAGER,

            UserRole.VETERINARIAN,

            UserRole.AI_TECHNICIAN,

        }:

            sections.add(
                DashboardSection.HERD
            )



        if self.can_view_financials(role):

            sections.add(
                DashboardSection.FINANCE
            )



        return sections

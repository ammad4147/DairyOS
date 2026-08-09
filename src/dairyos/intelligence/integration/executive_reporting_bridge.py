"""
DairyOS Executive Reporting Bridge

Integration adapter between intelligence
runtime outputs and existing dashboard
executive reporting models.

Does not contain reporting logic.
Delegates presentation responsibility.
"""


from dairyos.herd.dashboard.models.executive_report import (
    ExecutiveReport,
)



class ExecutiveReportingBridge:
    """
    Converts executive runtime models
    into reporting models.
    """



    def build_report(
        self,
        cockpit,
    ):

        return ExecutiveReport(

            farm_name=cockpit.farm_name,

            farm_status=(
                cockpit.risk_level
            ),

            health_score=(
                cockpit.health_score
            ),

            production_score=(
                cockpit.production_score
            ),

            reproduction_score=(
                cockpit.reproduction_score
            ),

            financial_score=(
                cockpit.financial_score
            ),

            pending_actions=len(
                cockpit.actions
            ),

            management_effectiveness=(
                cockpit.overall_score
            ),

            priority_message=(
                cockpit.summary
            ),
        )

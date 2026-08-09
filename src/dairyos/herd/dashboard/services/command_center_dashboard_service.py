from ..models.command_center_dashboard import CommandCenterDashboard



class CommandCenterDashboardService:



    def generate(

        self,

        executive_report,

        recommendations_count=0,

        historical_actions=0

    ):


        return CommandCenterDashboard(

            farm_name=executive_report.farm_name,

            farm_status=executive_report.farm_status,

            health_score=executive_report.health_score,

            production_score=executive_report.production_score,

            reproduction_score=executive_report.reproduction_score,

            financial_score=executive_report.financial_score,

            pending_actions=executive_report.pending_actions,

            recommendations_count=recommendations_count,

            historical_actions=historical_actions,

            effectiveness_score=executive_report.management_effectiveness,

            priority_message=executive_report.priority_message

        )

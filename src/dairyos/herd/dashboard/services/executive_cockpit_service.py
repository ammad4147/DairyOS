from ..models.executive_cockpit import ExecutiveCockpit

from .alert_priority_service import AlertPriorityService


class ExecutiveCockpitService:


    def calculate_health_score(
        self,
        health_alerts
    ):

        if health_alerts == 0:
            return 100

        if health_alerts <= 2:
            return 80

        return 60



    def calculate_reproduction_score(
        self,
        open_cows
    ):

        if open_cows <= 3:
            return 100

        if open_cows <= 6:
            return 75

        return 50



    def calculate_financial_score(
        self,
        financial_status
    ):

        if financial_status == "POSITIVE":
            return 100

        return 70



    def calculate_replacement_score(
        self,
        replacement_shortage
    ):

        if replacement_shortage:
            return 50

        return 100



    def generate(

        self,

        command,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False

    ):


        health = self.calculate_health_score(
            health_alerts
        )


        reproduction = self.calculate_reproduction_score(
            open_cows
        )


        financial = self.calculate_financial_score(
            command.financial_status
        )


        production = (
            100
            if command.production_status == "ACTIVE"
            else 80
        )


        replacement = self.calculate_replacement_score(
            replacement_shortage
        )


        overall = round(

            (

                health

                + reproduction

                + financial

                + production

                + replacement

            ) / 5

        )


        alerts = AlertPriorityService().generate(

            health_alerts,

            open_cows,

            replacement_shortage

        )


        return ExecutiveCockpit(

            farm_name=command.farm_name,

            overall_score=overall,

            health_score=health,

            production_score=production,

            reproduction_score=reproduction,

            financial_score=financial,

            risk_level=command.overall_risk,

            priority=(
                alerts[0].recommended_action
                if alerts
                else "Maintain operations"
            ),

            summary=f"Executive herd score {overall}/100",

            alerts=alerts

        )
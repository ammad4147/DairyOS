from ..models.farm_health_index import FarmHealthIndex
from ..models.command_status import CommandStatus


class CommandCenterIntelligenceService:


    def calculate_health_index(

        self,

        production_score,

        health_score,

        reproduction_score,

        financial_score

    ):


        total = round(

            (

                production_score * 0.40

                +

                health_score * 0.25

                +

                reproduction_score * 0.20

                +

                financial_score * 0.15

            )

        )


        return FarmHealthIndex(

            production_score,

            health_score,

            reproduction_score,

            financial_score,

            total

        )



    def evaluate_status(

        self,

        health_index,

        risk_level

    ):


        if risk_level == "HIGH" or health_index.overall_score < 60:

            return CommandStatus(

                "RED",

                "Critical operational attention required",

                "HIGH"

            )


        if risk_level == "MEDIUM" or health_index.overall_score < 80:

            return CommandStatus(

                "YELLOW",

                "Monitor operational performance",

                "MEDIUM"

            )


        return CommandStatus(

            "GREEN",

            "Operations performing normally",

            "LOW"

        )

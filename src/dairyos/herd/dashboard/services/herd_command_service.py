from ..models.herd_command import HerdCommand



class HerdCommandService:



    def generate_from_context(self, context):


        return self.generate(

            farm_name=context.farm_name,

            total_animals=context.total_animals,

            health_alerts=context.health_alerts,

            open_cows=context.open_cows,

            replacement_shortage=context.replacement_shortage,

            production_status=context.production_status,

            financial_status=context.financial_status

        )



    def generate_from_decision(

        self,

        context,

        decision

    ):


        from .command_decision_service import CommandDecisionService


        command = self.generate_from_context(

            context

        )


        return CommandDecisionService().apply_decision(

            command,

            decision

        )



    def generate(

        self,

        farm_name,

        total_animals,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        production_status="STABLE",

        financial_status="POSITIVE"

    ):


        health_status = "NORMAL"

        reproduction_status = "NORMAL"

        risk = "LOW"

        attention = "No immediate action required"



        if health_alerts > 0:

            health_status = "ATTENTION REQUIRED"

            risk = "MEDIUM"

            attention = "Review animal health alerts"



        if open_cows > 3:

            reproduction_status = "MONITOR"

            if risk == "LOW":

                risk = "MEDIUM"

                attention = "Review reproductive performance"



        if replacement_shortage:

            risk = "HIGH"

            attention = "Review replacement pipeline"



        return HerdCommand(

            farm_name=farm_name,

            total_animals=total_animals,

            production_status=production_status,

            health_status=health_status,

            reproduction_status=reproduction_status,

            financial_status=financial_status,

            overall_risk=risk,

            owner_attention=attention

        )

from ..models.executive_status import ExecutiveStatus



class ExecutiveIntelligenceService:



    def evaluate(

        self,

        health_status,

        feed_status,

        production_status,

        financial_status

    ):



        statuses = [

            health_status,

            feed_status,

            production_status,

            financial_status

        ]



        if "HIGH" in statuses or "NEGATIVE" in statuses:

            overall_status = "ATTENTION"

            priority_action = "Immediate management review required"



        elif "MEDIUM" in statuses or "ATTENTION" in statuses:

            overall_status = "MONITOR"

            priority_action = "Monitor identified risk areas"



        else:

            overall_status = "GOOD"

            priority_action = "Maintain current strategy"



        return ExecutiveStatus(

            health_status,

            feed_status,

            production_status,

            financial_status,

            overall_status,

            priority_action

        )

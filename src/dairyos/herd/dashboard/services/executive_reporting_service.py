from ..models.executive_report import ExecutiveReport



class ExecutiveReportingService:



    def generate(

        self,

        farm_name,

        health_score,

        production_score,

        reproduction_score,

        financial_score,

        pending_actions,

        effectiveness,

        priority_message

    ):



        overall = round(

            (

                health_score

                + production_score

                + reproduction_score

                + financial_score

                + effectiveness

            ) / 5

        )



        if overall >= 85:

            status = "GREEN"

        elif overall >= 70:

            status = "YELLOW"

        else:

            status = "RED"



        return ExecutiveReport(

            farm_name=farm_name,

            farm_status=status,

            health_score=health_score,

            production_score=production_score,

            reproduction_score=reproduction_score,

            financial_score=financial_score,

            pending_actions=pending_actions,

            management_effectiveness=effectiveness,

            priority_message=priority_message

        )

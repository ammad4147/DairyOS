from ..models.executive_decision import ExecutiveDecision


class ExecutiveDecisionService:


    def generate(

        self,

        farm_name,

        alerts=None,

        command=None

    ):


        alerts = alerts or []


        priority = "LOW"

        risk = "LOW"

        decision_required = False

        action = "Maintain current operations"

        impact = "No immediate business impact"

        horizon = "Routine monitoring"



        for alert in alerts:


            if alert.category == "REPLACEMENT":


                decision_required = True

                priority = "HIGH"

                risk = "HIGH"

                action = "Secure replacement animals"

                impact = "Protect future milk production capacity"

                horizon = "Immediate"


                break



            if alert.category == "HEALTH":


                decision_required = True

                priority = "HIGH"

                risk = "MEDIUM"

                action = "Review animal health interventions"

                impact = "Reduce production loss and animal risk"

                horizon = "Immediate"


                break



            if alert.category == "REPRODUCTION":


                decision_required = True

                priority = "MEDIUM"

                risk = "MEDIUM"

                action = "Review breeding performance"

                impact = "Protect future herd productivity"

                horizon = "30 days"



        return ExecutiveDecision(

            farm_name=farm_name,

            decision_required=decision_required,

            priority_level=priority,

            risk_level=risk,

            recommended_action=action,

            business_impact=impact,

            time_horizon=horizon

        )

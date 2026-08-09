from dairyos.intelligence.operations.orchestration.gateway.operations_orchestration_gateway import (
    OperationsOrchestrationGateway,
)


class DecisionOrchestrationBridge:
    """
    Bridges Decision Intelligence and
    Operations Orchestration.

    Converts intelligence recommendations
    into executable farm operational actions.

    Maintains compatibility with:

    - DecisionRecommendation
    - OperationalAction
    """


    def __init__(
        self,
        gateway: OperationsOrchestrationGateway,
    ):

        self.gateway = gateway



    def create_actions(
        self,
        decisions: list,
    ):

        actions = []


        for item in decisions:

            recommendation = (
                item["recommendation"]
            )


            #
            # DecisionRecommendation compatibility
            #
            if hasattr(
                recommendation,
                "category",
            ):

                action_type = (
                    recommendation.category
                )

                description = (
                    recommendation.recommendation
                )

                source_decision = (
                    recommendation.rationale
                )


            #
            # OperationalAction compatibility
            #
            else:

                action_type = (
                    recommendation.action_type
                )

                description = (
                    recommendation.description
                )

                source_decision = (
                    recommendation.source_decision
                )



            action = self.gateway.create_action(

                action_type=action_type,

                description=description,

                priority=(
                    recommendation.priority
                ),

                source_decision=source_decision,

            )


            actions.append(
                action
            )


        return actions

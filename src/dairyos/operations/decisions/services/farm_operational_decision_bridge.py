from dairyos.operations.decisions.models.decision_context import (
    DecisionContext,
)

from dairyos.operations.decisions.models.operational_decision import (
    OperationalDecision,
)

from dairyos.operations.decisions.services.operations_decision_service import (
    OperationsDecisionService,
)


class FarmOperationalDecisionBridge:
    """
    Translates farm operational intelligence decisions
    into enterprise decision domain objects.

    Flow:

        FarmOperationalState
                |
                v
        farm OperationalDecisionService
                |
                v
        FarmOperationalDecisionBridge
                |
                v
        OperationalDecision
                |
                v
        DecisionActionBridge


    Rules:

    - Does not mutate FarmOperationalState.
    - Does not execute actions.
    - Preserves decision source traceability.
    """


    def __init__(
        self,
        operations_decision_service: OperationsDecisionService | None = None,
    ):

        self.operations_decision_service = (
            operations_decision_service
            if operations_decision_service is not None
            else OperationsDecisionService()
        )


    def create_from_recommendation(
        self,
        recommendation: dict,
    ) -> OperationalDecision:

        context = DecisionContext(

            source=(
                recommendation.get(
                    "source",
                    "farm_operations",
                )
            ),

            category=(
                recommendation.get(
                    "title",
                    recommendation.get(
                        "type",
                        "Operational Decision",
                    ),
                )
            ),

            description=str(
                recommendation.get(
                    "details",
                    recommendation.get(
                        "action",
                        "",
                    ),
                )
            ),

            operational_impact=(
                recommendation.get(
                    "priority",
                    "NORMAL",
                )
            ),

        )


        return self.operations_decision_service.create_decision(

            context=context,

            priority=(
                recommendation.get(
                    "priority",
                    "MEDIUM",
                )
            ),

            owner_action_required=True,

        )


    def create_from_recommendations(
        self,
        recommendations: list[dict],
    ) -> list[OperationalDecision]:

        return [

            self.create_from_recommendation(
                recommendation
            )

            for recommendation in recommendations

        ]

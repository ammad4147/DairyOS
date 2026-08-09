from ..models.operations_command_view import (
    OperationsCommandView,
)


class OperationsCommandIntegrationService:
    """
    Combines operational signals into a unified command view.
    """


    def generate_view(
        self,
        operational_status: str = "GREEN",
        active_actions: int = 0,
        performance_score: float = 100.0,
    ) -> OperationsCommandView:


        if operational_status == "RED":

            return OperationsCommandView(
                operational_status="RED",
                priority_level="CRITICAL",
                active_actions=active_actions,
                performance_score=performance_score,
                management_attention_required=True,
                recommended_focus=(
                    "Resolve critical operational issues"
                ),
            )


        if operational_status == "AMBER":

            return OperationsCommandView(
                operational_status="AMBER",
                priority_level="HIGH",
                active_actions=active_actions,
                performance_score=performance_score,
                management_attention_required=True,
                recommended_focus=(
                    "Review operational exceptions"
                ),
            )


        return OperationsCommandView(
            operational_status="GREEN",
            priority_level="NORMAL",
            active_actions=active_actions,
            performance_score=performance_score,
            management_attention_required=False,
            recommended_focus=(
                "Maintain operational performance"
            ),
        )

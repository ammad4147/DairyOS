from ..models.executive_operations_summary import (
    ExecutiveOperationsSummary,
)

from ...command.services.operations_command_service import (
    OperationsCommandService,
)

from ...command_center.services.governance_attention_query_service import (
    GovernanceAttentionQueryService,
)


class ExecutiveOperationsService:
    """
    Builds executive operational summary.

    Read-side aggregation only.

    Does not:
    - execute actions
    - modify governance state
    - trigger escalation
    """


    def __init__(
        self,
        command_service: OperationsCommandService | None = None,
        governance_attention_service: GovernanceAttentionQueryService | None = None,
    ):

        self.command_service = (
            command_service
            if command_service is not None
            else OperationsCommandService()
        )


        self.governance_attention_service = (
            governance_attention_service
            if governance_attention_service is not None
            else GovernanceAttentionQueryService()
        )



    def generate_summary(
        self,
        governance_rules=None,
        escalation_policies=None,
    ):

        status = (
            self.command_service
            .generate_status()
        )


        critical_count = sum(

            1

            for attention in status.attentions

            if attention.priority.upper() == "CRITICAL"

        )


        governance_attention = (
            self.governance_attention_service
            .build_projection(
                governance_rules=governance_rules,
                escalation_policies=escalation_policies,
            )
        )


        governance_required = (
            governance_attention[
                "governance_attention_required"
            ]
        )


        governance_count = (
            governance_attention[
                "governance_attention_count"
            ]
        )


        if status.health_status == "RED":

            priority = 90.0

            owner_action = True

            focus = (
                "Immediate operational intervention required"
            )


        elif (
            status.health_status == "AMBER"
            or governance_required
        ):

            priority = 60.0

            owner_action = True

            focus = (
                "Review operational and governance exceptions"
            )


        else:

            priority = 10.0

            owner_action = False

            focus = (
                "Operations stable"
            )


        critical_items = [

            attention.title

            for attention in status.attentions

            if attention.priority.upper() == "CRITICAL"

        ]


        if governance_required:

            critical_items.append(
                f"Governance attention items: {governance_count}"
            )


        return ExecutiveOperationsSummary(

            health_status=status.health_status,

            attention_count=(
                status.active_attention_count
                +
                governance_count
            ),

            critical_issue_count=critical_count,

            owner_action_required=owner_action,

            recommended_focus=focus,

            operational_priority_score=priority,

            critical_items=critical_items,

        )

from dairyos.operations.command_center.services.governance_attention_query_service import (
    GovernanceAttentionQueryService,
)


class Rule:

    escalation_required = True



def test_governance_attention_projection():

    service = GovernanceAttentionQueryService()


    result = (
        service.build_projection(
            governance_rules=[
                Rule()
            ],
            escalation_policies=[
                "policy"
            ],
        )
    )


    assert (
        result["governance_attention_required"]
        is True
    )


    assert (
        result["governance_attention_count"]
        == 1
    )


    assert (
        result["governance_escalation_policy_count"]
        == 1
    )

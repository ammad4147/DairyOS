from dairyos.operations.command_center.services.governance_query_service import (
    GovernanceQueryService,
)


def test_governance_projection_contains_counts():

    service = GovernanceQueryService()


    projection = (
        service.build_projection(
            rules=[
                "rule-1",
                "rule-2",
            ],
            policies=[
                "policy-1",
            ],
            cycles=[
                "cycle-1",
            ],
            owners=[
                "owner-1",
                "owner-2",
            ],
        )
    )


    assert (
        projection["governance_rule_count"]
        == 2
    )


    assert (
        projection["escalation_policy_count"]
        == 1
    )


    assert (
        projection["review_cycle_count"]
        == 1
    )


    assert (
        projection["operational_owner_count"]
        == 2
    )

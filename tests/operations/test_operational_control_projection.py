from dairyos.operations.command_center.services.operational_control_query_service import (
    OperationalControlQueryService,
)


class Rule:

    escalation_required = True



def test_operational_control_projection():

    service = OperationalControlQueryService()


    projection = (
        service.build_projection(
            governance_rules=[
                Rule()
            ],
            escalation_policies=[
                "policy"
            ],
            review_cycles=[
                "weekly"
            ],
        )
    )


    assert (
        projection["control_rules"]
        == 1
    )


    assert (
        projection["control_escalation_policies"]
        == 1
    )


    assert (
        projection["control_review_cycles"]
        == 1
    )


    assert (
        projection["control_status"]
        == "ATTENTION"
    )

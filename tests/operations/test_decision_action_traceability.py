from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)


def test_action_preserves_decision_traceability():

    service = OperationalActionService()


    action = service.create_action(

        title="Investigate milk production drop",

        description="Review abnormal production decline",

        assigned_to="Farm Supervisor",

        department="Farm Operations",

        source_decision_id="DEC-0001",

    )


    assert action.action_id == "ACT-0001"

    assert action.source_decision_id == "DEC-0001"

from dairyos.operations.cockpit.services.executive_operations_cockpit_service import (
    ExecutiveOperationsCockpitService,
)


def test_executive_cockpit_green():

    service = ExecutiveOperationsCockpitService()

    cockpit = service.generate_cockpit()

    assert cockpit.overall_status == "GREEN"
    assert cockpit.action_required is False



def test_executive_cockpit_red():

    service = ExecutiveOperationsCockpitService()

    cockpit = service.generate_cockpit(
        control_status="RED",
    )

    assert cockpit.overall_status == "RED"
    assert cockpit.risk_level == "HIGH"
    assert cockpit.action_required is True

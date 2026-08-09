from dairyos.operations.control.models.control_attention import (
    ControlAttention,
)

from dairyos.operations.control.services.operations_control_service import (
    OperationsControlService,
)



def test_control_tower_green():

    service = OperationsControlService()

    status = service.generate_status()

    assert status.control_status == "GREEN"
    assert status.attention_required is False



def test_control_tower_critical():

    service = OperationsControlService()

    attention = ControlAttention(
        attention_id="CTRL-001",
        category="Animal Health",
        severity="CRITICAL",
        description="Critical health issue detected",
        recommended_action="Immediate veterinary review",
    )

    service.register_attention(attention)

    status = service.generate_status()

    assert status.control_status == "RED"
    assert status.priority_level == "CRITICAL"
    assert status.attention_required is True

from dairyos.farm.inputs.governance.input_governance_service import (
    InputGovernanceService,
)


class FakeEvent:

    input_type = "MILK_ENTRY"

    actor = "operator_1"

    source = "mobile_entry"



def test_operational_input_governance_records_audit():

    service = InputGovernanceService()


    record = service.record(
        FakeEvent()
    )


    assert record.input_type == "MILK_ENTRY"

    assert record.actor == "operator_1"

    assert record.source == "mobile_entry"

    assert record.accepted is True


    assert len(
        service.list_records()
    ) == 1

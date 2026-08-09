from dairyos.operations import (
    DailyOperation,
    DailyOperationsService,
)


def test_daily_operation_creation():

    operation = DailyOperation(
        operation_id="OP-001",
        operation_type="FEEDING",
        description="Morning feeding completed",
    )

    assert operation.operation_id == "OP-001"
    assert operation.operation_type == "FEEDING"



def test_daily_operation_service():

    service = DailyOperationsService()

    operation = DailyOperation(
        operation_id="OP-002",
        operation_type="MILKING",
        description="Morning milking",
    )

    service.add_operation(operation)

    operations = service.get_operations()

    assert len(operations) == 1
    assert operations[0].operation_id == "OP-002"



def test_complete_operation():

    service = DailyOperationsService()

    operation = DailyOperation(
        operation_id="OP-003",
        operation_type="HEALTH_CHECK",
        description="Veterinary inspection",
    )

    service.add_operation(operation)

    result = service.complete_operation(
        "OP-003",
        "Checked by farm veterinarian",
    )

    assert result is True

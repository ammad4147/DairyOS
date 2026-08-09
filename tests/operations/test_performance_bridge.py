from dairyos.operations.performance_integration.services.performance_bridge import (
    PerformanceBridge,
)


class FakeAccountabilityRecord:

    execution_id = "EXE-0001"

    staff_member = "Milking Operator"

    task_name = "Morning Milking"

    status = "COMPLETED"



def test_completed_execution_creates_performance_record():

    bridge = PerformanceBridge()

    record = bridge.evaluate_execution(
        FakeAccountabilityRecord()
    )


    assert record.execution_id == "EXE-0001"

    assert record.staff_member == "Milking Operator"

    assert record.task_name == "Morning Milking"

    assert record.completion_status == "COMPLETED"

    assert record.performance_score == 100.0



def test_performance_records_are_stored():

    bridge = PerformanceBridge()


    bridge.evaluate_execution(
        FakeAccountabilityRecord()
    )


    records = bridge.get_records()


    assert len(records) == 1

from dairyos.operations.command_center.services.execution_accountability_query_service import (
    ExecutionAccountabilityQueryService,
)


class FakeRecord:

    status = "COMPLETED"



def test_command_center_execution_accountability():

    service = ExecutionAccountabilityQueryService()


    result = service.build_projection(

        [
            FakeRecord()
        ]

    )


    assert result["execution_accountability_count"] == 1

    assert result["completed_execution_count"] == 1

    assert result["pending_execution_count"] == 0

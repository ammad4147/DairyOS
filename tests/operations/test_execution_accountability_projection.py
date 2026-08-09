from dairyos.operations.command_center.execution_accountability_projection import (
    ExecutionAccountabilityProjection,
)


class FakeRecord:

    status = "ASSIGNED"



def test_command_center_accountability_projection():

    projection = ExecutionAccountabilityProjection(

        records=[
            FakeRecord()
        ]

    )


    view = projection.build()


    assert view["total_assignments"] == 1

    assert view["completed_assignments"] == 0

    assert view["pending_assignments"] == 1

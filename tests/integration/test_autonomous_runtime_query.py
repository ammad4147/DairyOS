from dairyos.intelligence.integration.autonomous_runtime_query import (
    AutonomousRuntimeQuery,
)


def test_autonomous_runtime_query_creation():

    query = AutonomousRuntimeQuery()

    assert query is not None



def test_autonomous_runtime_query_status():

    query = AutonomousRuntimeQuery()

    status = query.get_status()

    assert (
        status["component"]
        == "autonomous_runtime_query"
    )

    assert (
        status["status"]
        == "operational"
    )

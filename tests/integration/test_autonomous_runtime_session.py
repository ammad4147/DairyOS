from dairyos.intelligence.integration.autonomous_runtime_session import (
    AutonomousRuntimeSession,
)


def test_autonomous_runtime_session_execution():

    session = AutonomousRuntimeSession()

    result = session.execute(
        []
    )

    assert result is not None

    assert "session" in result

    assert result["session"]["status"] == "completed"

    assert "result" in result



def test_autonomous_runtime_session_has_identity():

    session = AutonomousRuntimeSession()

    result = session.execute()

    assert (
        result["session"]["session_id"]
        is not None
    )

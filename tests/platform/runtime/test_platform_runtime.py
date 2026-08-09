from dairyos.platform.runtime import (
    PlatformRuntime,
)



def test_platform_runtime_starts():

    runtime = PlatformRuntime()

    state = runtime.start()

    assert state.active is True

    assert runtime.status() == "RUNNING"



def test_platform_runtime_stops():

    runtime = PlatformRuntime()

    runtime.start()

    state = runtime.stop()

    assert state.active is False

    assert runtime.status() == "STOPPED"



def test_platform_runtime_state_is_running():

    runtime = PlatformRuntime()

    state = runtime.start()

    assert state.is_running() is True

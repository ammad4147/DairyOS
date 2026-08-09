from dairyos.api.dependencies import get_container


def test_container_dependency_returns_started_container():
    container = get_container()

    assert container is not None
    assert container.started is True

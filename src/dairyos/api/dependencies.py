from dairyos.runtime.container import RuntimeContainer


def get_container():
    """
    FastAPI dependency returning the canonical RuntimeContainer.

    The application runtime owns database and service infrastructure.
    API dependencies must not create independent database connections.
    """

    from dairyos.app import container

    if not container.started:
        container.start()

    return container

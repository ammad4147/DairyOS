from dairyos.application.application_runtime import (
    ApplicationRuntime,
)

from dairyos.platform.bootstrap.services.enterprise_runtime_bootstrap import (
    EnterpriseRuntimeBootstrap,
)


def test_enterprise_runtime_bootstrap_starts():
    application_runtime = ApplicationRuntime()

    bootstrap = EnterpriseRuntimeBootstrap(
        application_runtime=application_runtime,
    )

    result = bootstrap.start()

    assert result.started is True

    assert result.runtime_ready is True

    assert result.services_loaded >= 1


def test_enterprise_runtime_bootstrap_registers_application_runtime():
    application_runtime = ApplicationRuntime()

    bootstrap = EnterpriseRuntimeBootstrap(
        application_runtime=application_runtime,
    )

    bootstrap.start()

    service = (
        bootstrap.registry
        .get(
            "application_runtime"
        )
    )

    assert service is not None

    assert (
        service.service
        is application_runtime
    )

    assert (
        bootstrap.application_runtime
        is application_runtime
    )

from dairyos.platform.integration.services.platform_registration_service import (
    PlatformRegistrationService,
)


class OperationsRegistration:

    """
    Registers DairyOS Operations Runtime
    with enterprise platform.
    """


    SERVICE_NAME = "operations_runtime"



    @staticmethod
    def register(
        registration_service: PlatformRegistrationService,
        operations_runtime,
    ):

        from dairyos.platform.integration.adapters.operations_runtime_adapter import (
            OperationsRuntimeAdapter,
        )


        registration_service.register_service(
            OperationsRegistration.SERVICE_NAME,
            OperationsRuntimeAdapter(
                operations_runtime
            ),
        )

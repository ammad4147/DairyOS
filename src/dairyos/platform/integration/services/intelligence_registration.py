from dairyos.platform.integration.services.platform_registration_service import (
    PlatformRegistrationService,
)


class IntelligenceRegistration:

    """
    Registers Intelligence Kernel
    with enterprise platform.
    """

    SERVICE_NAME = "intelligence_kernel"



    @staticmethod
    def register(
        registration_service: PlatformRegistrationService,
        kernel,
    ):

        from dairyos.platform.integration.adapters.intelligence_kernel_adapter import (
            IntelligenceKernelAdapter,
        )


        registration_service.register_service(
            IntelligenceRegistration.SERVICE_NAME,
            IntelligenceKernelAdapter(kernel),
        )

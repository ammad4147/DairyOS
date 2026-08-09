from dairyos.platform.domain_registry.services.default_domains import (
    DEFAULT_DOMAINS,
)



class DomainBootstrap:

    """
    Registers DairyOS operational domains.
    """



    def initialize(
        self,
        registry,
    ):


        for domain in DEFAULT_DOMAINS:

            registry.register(domain)



        return registry

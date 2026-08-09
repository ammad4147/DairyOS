from dairyos.platform.domain_registry.models.domain import Domain



class DomainRegistryService:
    """
    Enterprise domain discovery registry.
    """



    def __init__(self):

        self.domains = {}



    def register(
        self,
        domain: Domain,
    ):

        self.domains[
            domain.name
        ] = domain


        return domain



    def get(
        self,
        name: str,
    ):

        return self.domains.get(
            name
        )



    def list_domains(self):

        return list(
            self.domains.values()
        )

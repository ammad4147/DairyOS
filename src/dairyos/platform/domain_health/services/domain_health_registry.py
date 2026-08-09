class DomainHealthRegistry:
    """
    Stores domain health reports.
    """



    def __init__(self):

        self.records = {}



    def update(
        self,
        domain,
        status,
    ):

        self.records[domain] = status



    def get(
        self,
        domain,
    ):

        return self.records.get(domain)

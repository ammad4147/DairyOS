from dairyos.platform.resources.models.resource_limit import (
    ResourceLimit,
)


class ResourceService:
    """
    Enterprise resource capacity manager.
    """



    def __init__(self):

        self.limits = {}

        self.usage = {}



    def set_limit(
        self,
        limit: ResourceLimit,
    ):

        key = (
            limit.tenant_id,
            limit.resource_type,
        )

        self.limits[key] = limit



    def check_capacity(
        self,
        tenant_id: str,
        resource_type: str,
        requested: int,
    ):


        key = (
            tenant_id,
            resource_type,
        )


        limit = self.limits.get(
            key
        )


        if limit is None:

            return False



        current = self.usage.get(
            key,
            0,
        )


        return (
            current + requested
            <= limit.maximum
        )



    def consume(
        self,
        tenant_id: str,
        resource_type: str,
        amount: int,
    ):

        key = (
            tenant_id,
            resource_type,
        )


        self.usage[key] = (
            self.usage.get(key, 0)
            +
            amount
        )

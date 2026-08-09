from dairyos.platform.security_boundary.models.access_result import (
    AccessResult,
)



class AuthorizationService:
    """
    Enterprise operational authorization service.
    """



    def check(
        self,
        context,
        permission,
    ):


        if permission in context.permissions:

            return AccessResult(

                allowed=True,

                reason="Permission granted",

            )


        return AccessResult(

            allowed=False,

            reason="Permission denied",

        )


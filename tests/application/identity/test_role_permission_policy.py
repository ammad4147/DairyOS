from dairyos.application.identity.policies.role_permission_policy import (
    RolePermissionPolicy,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)

from dairyos.application.identity.policies.permission import (
    Permission,
)


def test_owner_can_view_financial_status():

    policy = RolePermissionPolicy()


    assert policy.can(

        UserRole.OWNER,

        Permission.VIEW_FINANCIAL_STATUS,

    )



def test_labourer_cannot_view_financial_status():

    policy = RolePermissionPolicy()


    assert not policy.can(

        UserRole.LABOURER,

        Permission.VIEW_FINANCIAL_STATUS,

    )

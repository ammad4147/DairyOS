from uuid import uuid4

from dairyos.application.identity.services.identity_bridge_service import (
    IdentityBridgeService,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)


def test_identity_bridge_creates_operational_user():

    service = IdentityBridgeService()


    user = service.from_identity(

        user_id=uuid4(),

        username="Farm Owner",

        role="owner",

    )


    assert user.name == "Farm Owner"

    assert user.role == UserRole.OWNER

    assert user.active is True



def test_identity_bridge_accepts_enum_role():

    service = IdentityBridgeService()


    user = service.from_identity(

        user_id=uuid4(),

        username="Manager",

        role=UserRole.FARM_MANAGER,

    )


    assert user.role == UserRole.FARM_MANAGER

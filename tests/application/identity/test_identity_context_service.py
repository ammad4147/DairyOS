from uuid import uuid4

from dairyos.application.identity.services.identity_context_service import (
    IdentityContextService,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)



def test_identity_context_creates_operational_user():

    service = IdentityContextService()


    user = service.create_user_context(

        user_id=uuid4(),

        username="Farm Manager",

        role="farm_manager",

    )


    assert user.name == "Farm Manager"

    assert user.role == UserRole.FARM_MANAGER



def test_identity_context_creates_dashboard_context():

    service = IdentityContextService()


    user = service.create_user_context(

        user_id=uuid4(),

        username="Owner",

        role=UserRole.OWNER,

    )


    context = service.create_dashboard_context(
        user
    )


    assert context.user_id == user.user_id

    assert context.role == UserRole.OWNER

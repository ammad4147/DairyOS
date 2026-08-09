from uuid import uuid4

from dairyos.application.identity.models.user_session import (
    UserSession,
)

from dairyos.application.identity.models.user_role import (
    UserRole,
)



def test_user_session_creates_operational_context():

    session = UserSession(
        user_id=uuid4(),
        user_name="Ahmed",
        role=UserRole.FARM_MANAGER,
    )


    assert session.user_name == "Ahmed"

    assert session.role == UserRole.FARM_MANAGER

    assert session.active

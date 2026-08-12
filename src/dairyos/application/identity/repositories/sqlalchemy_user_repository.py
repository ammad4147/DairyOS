from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from dairyos.application.identity.models.operational_user import OperationalUser
from dairyos.application.identity.models.authorization_role import AuthorizationRole
from dairyos.data.database.models.user_account_model import UserAccountModel


class SqlAlchemyUserRepository:
    """Database-backed repository for authenticated operational users."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        farm_id: str,
        username: str,
        display_name: str,
        password_hash: str,
        role: AuthorizationRole,
    ) -> UserAccountModel:
        account = UserAccountModel(
            user_id=str(uuid4()),
            farm_id=farm_id,
            username=username,
            display_name=display_name,
            password_hash=password_hash,
            role=role.value,
            active=True,
        )
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def get_by_username(self, *, farm_id: str, username: str) -> UserAccountModel | None:
        return self.session.scalar(
            select(UserAccountModel).where(
                UserAccountModel.farm_id == farm_id,
                UserAccountModel.username == username,
            )
        )

    def get_by_id(self, user_id: UUID | str) -> UserAccountModel | None:
        return self.session.get(UserAccountModel, str(user_id))

    def list_for_farm(self, farm_id: str) -> list[UserAccountModel]:
        return list(
            self.session.scalars(
                select(UserAccountModel)
                .where(UserAccountModel.farm_id == farm_id)
                .order_by(UserAccountModel.username)
            )
        )

    @staticmethod
    def to_context(account: UserAccountModel) -> dict[str, str | bool]:
        return {
            "sub": account.user_id,
            "username": account.username,
            "name": account.display_name,
            "role": account.role,
            "farm_id": account.farm_id,
            "active": account.active,
        }

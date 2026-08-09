from dairyos.operations.users.models.operational_user import (
    OperationalUser,
)


class OperationalUserService:
    """
    Application service for operational users.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def create_user(
        self,
        name,
        role,
    ):

        user = OperationalUser(

            name=name,

            role=role,

        )


        return self.repository.save(
            user
        )



    def get_user(
        self,
        user_id,
    ):

        return self.repository.get(
            user_id
        )



    def list_users(
        self,
    ):

        return self.repository.all()

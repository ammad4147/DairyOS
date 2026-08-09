class OperationalUserRepository:
    """
    Stores operational farm users.
    """


    def __init__(
        self,
    ):

        self._users = {}



    def save(
        self,
        user,
    ):

        self._users[
            user.user_id
        ] = user


        return user



    def get(
        self,
        user_id,
    ):

        return self._users.get(
            user_id
        )



    def all(
        self,
    ):

        return list(
            self._users.values()
        )

from ..models.user import User


class UserRepository:
    """Persistence for the minimal D3 user/RBAC model."""

    def __init__(self, session=None):

        self.session = session
        self.records = []

    def add(self, user):

        if self.session:
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user

        self.records.append(user)
        return user

    def get_all(self):

        if self.session:
            return self.session.query(User).all()

        return self.records

    def get_by_username(self, username):

        if self.session:
            return (
                self.session.query(User)
                .filter(User.username == username)
                .first()
            )

        for item in self.records:
            if getattr(item, "username", None) == username:
                return item

        return None

    def exists_username(self, username):

        return self.get_by_username(username) is not None

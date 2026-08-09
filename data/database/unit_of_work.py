from dairyos.data.database.session import SessionLocal
from dairyos.data.database.repositories.sqlalchemy_milk_repository import SQLAlchemyMilkRepository
from dairyos.data.database.repositories.sqlalchemy_feed_repository import SQLAlchemyFeedRepository

class UnitOfWork:
    def __init__(self):
        self.session_factory = SessionLocal

    def __enter__(self):
        self.session = self.session_factory()
        self.milk = SQLAlchemyMilkRepository(self.session)
        self.feed = SQLAlchemyFeedRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

from dairyos.farm.operations.repositories.feed_repository import (
    FeedRepository,
)

from dairyos.data.models import (
    FeedRecord as DatabaseFeedRecord,
)


class DatabaseFeedRepository(
    FeedRepository,
):
    """
    PostgreSQL-backed feed repository adapter.
    """


    def __init__(
        self,
        session,
    ):

        self.session = session



    def save(
        self,
        record,
    ):

        feed = DatabaseFeedRecord(

            group_or_pen=(
                record.animal_group
            ),

            feed_type=(
                record.feed_type
            ),

            quantity_kg=(
                record.quantity_kg
            ),

            feeding_date=(
                record.timestamp.replace(
                    tzinfo=None
                )
            ),

        )


        self.session.add(
            feed
        )

        self.session.commit()

        self.session.refresh(
            feed
        )


        return record



    def get_all(
        self,
    ):

        return (
            self.session.query(
                DatabaseFeedRecord
            )
            .all()
        )

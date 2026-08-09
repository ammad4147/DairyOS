from ..database.models.operational_event_model import (
    OperationalEventModel,
)


class OperationalEventRepository:
    """
    Persistence boundary for operational events.

    Accepts domain FarmOperationEvent objects
    and translates them into database-safe records.

    Supports:
    - SQLAlchemy persistence
    - in-memory testing mode
    """


    def __init__(
        self,
        session=None,
    ):

        self.session = session

        self.records = []



    def _to_model(
        self,
        event,
    ):

        return OperationalEventModel(

            event_type=event.event_type,

            source="FARM_OPERATIONS",

            description=self._build_description(
                event
            ),

            created_at=event.timestamp.replace(
                tzinfo=None
            ),

        )



    def _build_description(
        self,
        event,
    ):

        description = (
            f"{event.event_type}"
        )


        if event.animal_id:

            description += (
                f" animal={event.animal_id}"
            )


        if event.operator:

            description += (
                f" operator={event.operator}"
            )


        return description



    def add(
        self,
        event,
    ):

        if self.session:

            model = self._to_model(
                event
            )

            self.session.add(
                model
            )

            self.session.commit()

            return model


        self.records.append(
            event
        )

        return event



    def get_all(
        self,
    ):

        if self.session:

            return (
                self.session.query(
                    OperationalEventModel
                )
                .all()
            )


        return self.records



    def count(
        self,
    ):

        if self.session:

            return (
                self.session.query(
                    OperationalEventModel
                )
                .count()
            )


        return len(
            self.records
        )

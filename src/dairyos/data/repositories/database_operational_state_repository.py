from datetime import datetime, date, timezone

from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)

from dairyos.data.database.models.operational_state_model import (
    OperationalStateModel,
)


class DatabaseOperationalStateRepository:
    """
    SQLAlchemy persistence adapter
    for current operational state.

    Persists the current FarmOperationalState
    JSON projection.

    Historical events remain separate.
    """

    def __init__(
        self,
        session,
    ):

        self.session = session


    def _serialize(
        self,
        value,
    ):
        """
        Convert operational state payload
        into JSON compatible primitives.
        """

        if isinstance(
            value,
            datetime,
        ):
            return value.isoformat()


        if isinstance(
            value,
            date,
        ):
            return value.isoformat()


        if isinstance(
            value,
            dict,
        ):
            return {
                key: self._serialize(item)
                for key, item in value.items()
            }


        if isinstance(
            value,
            list,
        ):
            return [
                self._serialize(item)
                for item in value
            ]


        return value



    def get_current(
        self,
        farm_id: str,
    ):

        record = (
            self.session.query(
                OperationalStateModel
            )
            .filter(
                OperationalStateModel.farm_id
                ==
                farm_id
            )
            .first()
        )


        if record is None:

            return None


        payload = record.state_payload or {}


        state = FarmOperationalState(
            farm_id=record.farm_id,
            operational_date=record.operational_date,
        )


        state.milk_status = payload.get(
            "milk_status",
            {},
        )

        state.feeding_status = payload.get(
            "feeding_status",
            {},
        )

        state.health_alerts = payload.get(
            "health_alerts",
            [],
        )

        state.breeding_status = payload.get(
            "breeding_status",
            {},
        )

        state.workforce_status = payload.get(
            "workforce_status",
            {},
        )

        state.inventory_status = payload.get(
            "inventory_status",
            {},
        )

        state.equipment_status = payload.get(
            "equipment_status",
            {},
        )

        state.financial_status = payload.get(
            "financial_status",
            {},
        )

        state.operational_freshness = payload.get(
            "operational_freshness",
            {},
        )

        state.milk_production_summary = payload.get(
            "milk_production_summary",
            {},
        )

        state.open_tasks = payload.get(
            "open_tasks",
            [],
        )

        state.completed_tasks = payload.get(
            "completed_tasks",
            [],
        )

        state.heads_up_notifications = payload.get(
            "heads_up_notifications",
            [],
        )

        state.exceptions = payload.get(
            "exceptions",
            [],
        )


        return state



    def save(
        self,
        state: FarmOperationalState,
    ):

        payload = self._serialize(
            {
                "milk_status": state.milk_status,
                "feeding_status": state.feeding_status,
                "health_alerts": state.health_alerts,
                "breeding_status": state.breeding_status,
                "workforce_status": state.workforce_status,
                "inventory_status": state.inventory_status,
                "equipment_status": state.equipment_status,
                "financial_status": state.financial_status,
                "operational_freshness": state.operational_freshness,
                "milk_production_summary": state.milk_production_summary,
                "open_tasks": state.open_tasks,
                "completed_tasks": state.completed_tasks,
                "heads_up_notifications": state.heads_up_notifications,
                "exceptions": state.exceptions,
            }
        )


        existing = (
            self.session.query(
                OperationalStateModel
            )
            .filter(
                OperationalStateModel.farm_id
                ==
                state.farm_id
            )
            .first()
        )


        if existing:

            existing.operational_date = (
                state.operational_date
            )

            existing.state_payload = payload

            self.session.commit()

            return state



        record = OperationalStateModel(

            farm_id=state.farm_id,

            operational_date=state.operational_date,

            state_payload=payload,

            created_at=datetime.now(
                timezone.utc
            ).replace(
                tzinfo=None
            ),

        )


        self.session.add(
            record
        )

        self.session.commit()


        return state
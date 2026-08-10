from dataclasses import dataclass, field
from datetime import datetime, timezone

from .operational_schedule_state import OperationalScheduleState


def _serialize(value):

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: _serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _serialize(item)
            for item in value
        ]

    return value


@dataclass
class FarmOperationalState:

    farm_id: str

    operational_date: str


    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )


    active_operations: dict = field(
        default_factory=dict
    )


    animals: dict = field(
        default_factory=dict
    )


    milk_status: dict = field(
        default_factory=dict
    )


    feeding_status: dict = field(
        default_factory=dict
    )


    health_state: dict = field(
        default_factory=dict
    )


    health_alerts: list = field(
        default_factory=list
    )


    breeding_status: dict = field(
        default_factory=dict
    )


    workforce_status: dict = field(
        default_factory=dict
    )


    inventory_status: dict = field(
        default_factory=dict
    )


    equipment_status: dict = field(
        default_factory=dict
    )


    financial_status: dict = field(
        default_factory=dict
    )


    operational_freshness: dict = field(
        default_factory=dict
    )


    milk_production_summary: dict = field(
        default_factory=lambda: {
            "total_litres_today": 0,
            "milking_events_count": 0,
            "last_milking_time": None,
            "last_operator": None,
            "last_shift": None,
            "last_animal_id": None,
        }
    )


    open_tasks: list = field(
        default_factory=list
    )


    completed_tasks: list = field(
        default_factory=list
    )


    heads_up_notifications: list = field(
        default_factory=list
    )


    exceptions: list = field(
        default_factory=list
    )

    unhandled_events: list = field(
        default_factory=list
    )

    schedule_state: OperationalScheduleState | None = None



    def __post_init__(self):

        if self.schedule_state is None:

            self.schedule_state = OperationalScheduleState(
                schedule_date=self.operational_date
            )

    def record_lifecycle_event(
        self,
        animal_id,
        details,
    ):

        if animal_id is None:
            return None


        current = self.animals.setdefault(
            animal_id,
            {}
        )


        current["lifecycle"] = {

            "previous_status":
                details.get(
                    "previous_status"
                ),

            "new_status":
                details.get(
                    "new_status"
                ),

            "location":
                details.get(
                    "location"
                ),

            "operator":
                details.get(
                    "operator"
                ),

            "timestamp":
                details.get(
                    "timestamp"
                ),

        }


        return current["lifecycle"]

    def record_animal(
        self,
        animal_id,
        details,
    ):

        self.animals[animal_id] = details

        return self.animals[animal_id]


    def get_animal(
        self,
        animal_id,
    ):

        return self.animals.get(
            animal_id
        )


    def list_animals(
        self,
    ):

        return list(
            self.animals.values()
        )


    def start_operation(
        self,
        operation_type,
        operator=None,
        metadata=None,
    ):

        self.active_operations[operation_type] = {

            "status":
                "IN_PROGRESS",

            "operator":
                operator,

            "started_at":
                datetime.now(timezone.utc),

            "metadata":
                metadata or {},

        }

        return self.active_operations[operation_type]



    def complete_operation(
        self,
        operation_type,
    ):

        operation = self.active_operations.get(
            operation_type
        )

        if operation is not None:

            operation["status"] = "COMPLETED"

            operation["completed_at"] = (
                datetime.now(timezone.utc)
            )

        return operation



    def record_freshness(
        self,
        area,
        timestamp=None,
        source=None,
    ):

        self.operational_freshness[area] = {

            "last_updated":
                timestamp
                or datetime.now(timezone.utc),

            "source":
                source,

        }



    def record_milk_activity(
        self,
        shift,
        litres,
        operator=None,
        animal_id=None,
        timestamp=None,
    ):

        entry = self.milk_status.setdefault(

            shift,

            {

                "status":
                    "completed",

                "litres":
                    0,

                "animals_milked":
                    0,

                "unique_animal_ids":
                    [],

                "operators":
                    [],

                "last_timestamp":
                    None,

            }

        )


        entry["litres"] += litres

        if "unique_animal_ids" not in entry or not isinstance(entry["unique_animal_ids"], list):
            entry["unique_animal_ids"] = list(entry.get("unique_animal_ids") or [])

        if animal_id:
            str_id = str(animal_id)
            if str_id not in entry["unique_animal_ids"]:
                entry["unique_animal_ids"].append(str_id)
            entry["animals_milked"] = len(entry["unique_animal_ids"])
        else:
            entry["animals_milked"] += 1


        if operator and operator not in entry["operators"]:

            entry["operators"].append(
                operator
            )


        entry["last_timestamp"] = (
            timestamp
            or datetime.now(timezone.utc)
        )


        entry["status"] = "completed"


        self.milk_production_summary[
            "total_litres_today"
        ] += litres


        self.milk_production_summary[
            "milking_events_count"
        ] += 1


        self.milk_production_summary[
            "last_milking_time"
        ] = entry["last_timestamp"]


        self.milk_production_summary[
            "last_operator"
        ] = operator


        self.milk_production_summary[
            "last_shift"
        ] = shift


        self.milk_production_summary[
            "last_animal_id"
        ] = animal_id


        return entry

    def record_feed_activity(
        self,
        feed_type,
        quantity_kg,
    ):

        entry = self.feeding_status.setdefault(

            feed_type,

            {
                "status":
                    "completed",

                "quantity_kg":
                    0,

            }

        )


        entry["quantity_kg"] += quantity_kg

        entry["status"] = "completed"


        return entry



    def add_health_alert(
        self,
        animal_id,
        observation,
        severity,
    ):

        record = {

            "animal_id":
                animal_id,

            "observation":
                observation,

            "severity":
                severity,

            "timestamp":
                datetime.now(timezone.utc),

        }


        self.health_alerts.append(
            record
        )


        self.health_state[animal_id] = record


        return record


    def record_reproductive_event(
        self,
        animal_id,
        details,
    ):

        if animal_id is None:
            return None


        existing = self.breeding_status.setdefault(
            animal_id,
            {}
        )


        existing.update(
            details
        )


        existing["animal_id"] = animal_id


        existing["updated_at"] = (
            datetime.now(timezone.utc)
        )


        return existing

    def record_breeding_activity(
        self,
        animal_id,
        details,
    ):

        self.breeding_status[animal_id] = {

            **details,

            "animal_id":
                animal_id,

            "updated_at":
                datetime.now(timezone.utc),

        }


        return self.breeding_status[animal_id]



    def record_workforce_activity(
        self,
        metric_type,
        value,
    ):

        self.workforce_status[metric_type] = value

        return value



    def record_inventory_status(
        self,
        inventory_type,
        item,
        details,
    ):

        key = inventory_type


        self.inventory_status[key] = {

            **details,

            "item":
                item,

            "status":
                details.get(
                    "status",
                    "UNKNOWN",
                ),

            "updated_at":
                datetime.now(timezone.utc),

        }


        return self.inventory_status[key]



    def record_equipment_status(
        self,
        equipment_id,
        details,
    ):

        self.equipment_status[equipment_id] = {

            **details,

            "updated_at":
                datetime.now(timezone.utc),

        }


        return self.equipment_status[equipment_id]



    def record_financial_activity(
        self,
        financial_type,
        details,
    ):

        self.financial_status[financial_type] = details

        return details



    def record_open_task(
        self,
        task,
    ):

        self.open_tasks.append(
            task
        )



    def record_completed_task(
        self,
        task,
    ):

        self.completed_tasks.append(
            task
        )



    def milk_total(
        self,
    ):

        return sum(

            record.get(
                "litres",
                0,
            )

            for record in self.milk_status.values()

        )



    def feed_total(
        self,
    ):

        return sum(

            record.get(
                "quantity_kg",
                0,
            )

            for record in self.feeding_status.values()

        )



    def health_status(
        self,
    ):

        if self.health_alerts:

            return "ATTENTION"

        return "NORMAL"



    def health_alert_count(
        self,
    ):

        return len(
            self.health_alerts
        )



    def operational_status(
        self,
    ):

        if self.exceptions:

            return "attention"

        return "normal"



    def heads_up_count(
        self,
    ):

        return len(
            self.heads_up_notifications
        )



    def record_event(
        self,
        event,
        payload=None,
    ):

        if isinstance(event, str):

            event_type = event
            event_payload = payload or {}

        else:

            event_type = (
                getattr(
                    event,
                    "event_type",
                    None,
                )
                or getattr(
                     event,
                     "name",
                     None,
                )
            )


            if event_type:

                import re

                event_type = re.sub(
                    r"(?<!^)(?=[A-Z])",
                    "_",
                    event_type,
                )

                event_type = (
                    event_type
                    .replace("-", "_")
                    .replace(" ", "_")
                    .lower()
                )

            event_payload = getattr(
                event,
                "payload",
                {},
            )


        animal_id = (
            getattr(event, "animal_id", None)
            or event_payload.get(
                "animal_id"
            )
        )


        if event_type == "activity_started":

            self.start_operation(
                event_payload.get("activity_type"),
                event_payload.get("operator"),
                event_payload,
            )


        elif event_type == "activity_completed":

            self.complete_operation(
                event_payload.get("activity_type")
            )


        elif event_type == "animal_created":

            self.record_animal(
                animal_id,
                event_payload,
            )


        elif event_type in (
            "milk_recorded",
            "milk_activity_recorded",
        ):

            self.record_milk_activity(

                event_payload.get(
                    "shift"
                )
                or event_payload.get(
                    "session"
                ),

                event_payload.get(
                    "litres",
                    0,
                ),

                event_payload.get(
                    "operator"
                ),

                animal_id,

                event_payload.get(
                    "timestamp"
                ),

            )


        elif event_type in (
            "feed_recorded",
            "feed_distributed",
        ):

            self.record_feed_activity(

                event_payload.get(
                    "feed_type"
                ),

                event_payload.get(
                    "quantity_kg",
                    0,
                ),

            )


        elif event_type in (
            "health_recorded",
            "health_observation_recorded",
        ):

            self.add_health_alert(
                animal_id,
                event_payload.get(
                    "observation",
                    "",
                ),
                event_payload.get(
                    "severity",
                    "warning",
                ),
            )


        elif event_type in (
            "breeding_recorded",
            "breeding_activity_recorded",
        ):

            self.record_breeding_activity(
                animal_id,
                event_payload,
            )

        elif event_type == "lifecycle_changed":

            self.record_lifecycle_event(
                animal_id,
                {
                    **event_payload,
                    "operator":
                        getattr(
                            event,
                            "operator",
                            None,
                        ),

                    "timestamp":
                        getattr(
                            event,
                            "timestamp",
                            None,
                        ),
                },
            )


        elif event_type in (
            "heat_detected",
            "insemination_recorded",
            "pregnancy_confirmed",
        ):

            self.record_reproductive_event(
                animal_id,
                {
                    **event_payload,
                    "event_type":
                        event_type,

                    "operator":
                        getattr(
                            event,
                            "operator",
                            None,
                        ),

                    "timestamp":
                        getattr(
                            event,
                            "timestamp",
                            None,
                        ),
                },
            )


        elif event_type == "workforce_activity_recorded":

            self.record_workforce_activity(
                event_payload.get("metric_type"),
                event_payload.get("value"),
            )


        elif event_type == "inventory_status_recorded":

            self.record_inventory_status(
                event_payload.get("inventory_type"),
                event_payload.get("item"),
                event_payload.get("details", {}),
            )


        elif event_type == "equipment_status_recorded":

            equipment_details = event_payload.get(
                "details",
                {},
            )

            if not equipment_details.get(
                "operator"
            ):

                operator = getattr(
                    event,
                    "operator",
                    None,
                )

                if operator:
                    equipment_details["operator"] = operator


            self.record_equipment_status(
                event_payload.get(
                    "equipment_id"
                ),
                equipment_details,
            )


        elif event_type in (
            "financial_status_recorded",
            "financial_transaction_recorded",
            "cash_position_recorded",
            "expense_recorded",
            "revenue_recorded",
        ):

            self.record_financial_activity(
                event_payload.get(
                    "financial_type"
                ),
                event_payload.get(
                    "details",
                    {},
                ),
            )


        elif event_type == "task_created":

            self.record_open_task(
                event_payload
            )


        elif event_type == "task_completed":

            self.record_completed_task(
                event_payload
            )


        if event_type not in (
            "activity_started",
            "activity_completed",
            "animal_created",
            "milk_recorded",
            "milk_activity_recorded",
            "feed_recorded",
            "feed_distributed",
            "health_recorded",
            "health_observation_recorded",
            "breeding_recorded",
            "breeding_activity_recorded",
            "lifecycle_changed",
            "heat_detected",
            "insemination_recorded",
            "pregnancy_confirmed",
            "workforce_activity_recorded",
            "inventory_status_recorded",
            "equipment_status_recorded",
            "financial_status_recorded",
            "financial_transaction_recorded",
            "cash_position_recorded",
            "expense_recorded",
            "revenue_recorded",
            "task_created",
            "task_completed",
        ):

            self.unhandled_events.append(
                {
                    "event_type":
                        event_type,

                    "event_id":
                        getattr(
                            event,
                            "event_id",
                            None,
                        ),

                    "timestamp":
                        getattr(
                            event,
                            "timestamp",
                            None,
                        ),
                }
            )


        return self


    def summary(
        self,
    ):

        return _serialize({

            "farm_id":
                self.farm_id,

            "operational_date":
                self.operational_date,

            "milk_status":
                self.milk_status,

            "feeding_status":
                self.feeding_status,

            "health_status":
                self.health_state,

            "breeding_status":
                self.breeding_status,

            "workforce_status":
                self.workforce_status,

            "inventory_status":
                self.inventory_status,

            "equipment_status":
                self.equipment_status,

            "financial_status":
                self.financial_status,

            "milk_production_summary":
                self.milk_production_summary,

            "open_tasks":
                self.open_tasks,

            "completed_tasks":
                self.completed_tasks,

            "animals":
                self.animals,

        })


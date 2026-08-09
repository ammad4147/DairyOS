from .farm_operational_state import FarmOperationalState


class OperationalStateEventService:
    """
    Translates operational events into FarmOperationalState updates.

    All operational changes must flow through
    FarmOperationalState event handling.

    This service does not create farm facts.
    It only records manually entered operational events.
    """


    def __init__(
        self,
        state: FarmOperationalState,
    ):

        self.state = state



    def record_milk_event(
        self,
        shift,
        litres,
        animal_id=None,
        operator=None,
        timestamp=None,
    ):

        self.state.record_event(
            "milk_recorded",
            {
                "shift": shift,

                "litres": litres,

                "animal_id": animal_id,

                "operator": operator,

                "timestamp": timestamp,

            },
        )



    def record_feed_event(
        self,
        feed_type,
        quantity_kg,
    ):

        self.state.record_event(
            "feed_distributed",
            {
                "feed_type": feed_type,
                "quantity_kg": quantity_kg,
            },
        )



    def record_health_event(
        self,
        animal_id,
        observation,
        severity,
    ):

        self.state.record_event(
            "health_observation_recorded",
            {
                "animal_id": animal_id,
                "observation": observation,
                "severity": severity,
            },
        )



    def record_breeding_event(
        self,
        animal_id,
        details,
    ):

        self.state.record_event(
            "breeding_recorded",
            {
                **details,
                "animal_id": animal_id,
            },
        )



    def record_workforce_event(
        self,
        metric_type,
        value,
    ):

        self.state.record_event(
            "workforce_activity_recorded",
            {
                "metric_type": metric_type,
                "value": value,
            },
        )



    def record_inventory_event(
        self,
        inventory_type,
        item,
        details,
    ):

        self.state.record_event(
            "inventory_status_recorded",
            {
                "inventory_type": inventory_type,
                "item": item,
                "details": details,
            },
        )



    def record_equipment_event(
        self,
        equipment_id,
        details,
    ):

        self.state.record_event(
            "equipment_status_recorded",
            {
                "equipment_id": equipment_id,
                "details": details,
            },
        )



    def record_task_created(
        self,
        task,
    ):
        """
        Add manually entered operational task
        into live farm state.
        """

        self.state.record_open_task(
            task
        )



    def record_task_completed(
        self,
        task,
    ):
        """
        Move completed task into completed history.
        """

        self.state.record_completed_task(
            task
        )



    def record_task_cancelled(
        self,
        task,
    ):
        """
        Track cancelled tasks as operational exceptions.
        """

        self.state.add_exception(
            {
                "type": "TASK_CANCELLED",
                "task": task,
            }
        )

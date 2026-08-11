from datetime import date

from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class OperationalStateRuntime:
    """
    Runtime owner for current farm operational state.

    Converts operational activity into current farm reality.

    Historical events remain separate.

    Persistence is optional:
        - repository provided:
            state is restored and saved
        - repository absent:
            existing in-memory behavior remains

    This component answers:

    "What is true about the farm now?"
    """

    def __init__(
        self,
        farm_id="TRIDENT-DAIRIES",
        repository=None,
    ):
        self.farm_id = farm_id
        self.repository = repository
        self.current_state = None

    def initialize(
        self,
        operational_date=None,
    ):
        if operational_date is None:
            operational_date = str(date.today())

        if self.repository is not None:
            existing_state = self.repository.get_current(
                self.farm_id
            )

            if existing_state is not None:
                existing_date = str(
                    existing_state.operational_date
                )

                if existing_date == operational_date:
                    self.current_state = existing_state
                    return self.current_state

                # A persisted state belongs to a previous
                # operational day. Start a fresh daily state.
                self.current_state = FarmOperationalState(
                    farm_id=self.farm_id,
                    operational_date=operational_date,
                )

                self.persist_state()

                return self.current_state

        self.current_state = FarmOperationalState(
            farm_id=self.farm_id,
            operational_date=operational_date,
        )

        self.persist_state()

        return self.current_state

    def ensure_state(
        self,
    ):
        today = str(date.today())

        if self.current_state is None:
            return self.initialize(
                operational_date=today
            )

        if str(
            self.current_state.operational_date
        ) != today:
            return self.initialize(
                operational_date=today
            )

        return self.current_state

    def persist_state(
        self,
    ):
        if (
            self.repository is not None
            and self.current_state is not None
        ):
            self.repository.save(
                self.current_state
            )

    def apply_milk_activity(
        self,
        shift,
        litres,
    ):
        state = self.ensure_state()

        state.record_milk_activity(
            shift=shift,
            litres=litres,
        )

        self.persist_state()

        return state

    def apply_feed_activity(
        self,
        feed_type,
        quantity_kg,
    ):
        state = self.ensure_state()

        state.record_feed_activity(
            feed_type=feed_type,
            quantity_kg=quantity_kg,
        )

        self.persist_state()

        return state

    def apply_health_alert(
        self,
        animal_id,
        observation,
        severity,
    ):
        state = self.ensure_state()

        state.add_health_alert(
            animal_id=animal_id,
            observation=observation,
            severity=severity,
        )

        self.persist_state()

        return state

    def apply_breeding_activity(
        self,
        animal_id,
        event_type,
        result,
        technician,
    ):
        state = self.ensure_state()

        state.record_breeding_activity(
            animal_id=animal_id,
            details={
                "event_type": event_type,
                "result": result,
                "technician": technician,
            },
        )

        self.persist_state()

        return state

    def apply_workforce_activity(
        self,
        metric_type,
        value,
    ):
        state = self.ensure_state()

        state.record_workforce_activity(
            metric_type=metric_type,
            value=value,
        )

        self.persist_state()

        return state

    def apply_inventory_status(
        self,
        inventory_type,
        item,
        details,
    ):
        state = self.ensure_state()

        state.record_inventory_status(
            inventory_type=inventory_type,
            item=item,
            details=details,
        )

        self.persist_state()

        return state

    def apply_equipment_status(
        self,
        equipment_id,
        details,
    ):
        state = self.ensure_state()

        state.record_equipment_status(
            equipment_id=equipment_id,
            details=details,
        )

        self.persist_state()

        return state

    def apply_financial_activity(
        self,
        financial_type,
        details,
    ):
        state = self.ensure_state()

        state.record_financial_activity(
            financial_type=financial_type,
            details=details,
        )

        self.persist_state()

        return state

    def create_task(
        self,
        task,
    ):
        state = self.ensure_state()

        state.record_open_task(
            task
        )

        self.persist_state()

        return state

    def complete_task(
        self,
        task,
    ):
        state = self.ensure_state()

        state.record_completed_task(
            task
        )

        self.persist_state()

        return state

    def get_state(
        self,
    ):
        return self.ensure_state()

    def get_summary(
        self,
    ):
        return self.ensure_state().summary()

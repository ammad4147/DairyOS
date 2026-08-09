
from datetime import datetime, UTC

from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)


class AnimalEventProjection:
    """
    Converts operational events into animal operational state.

    Projection flow:

        Operational Event
              |
              v
        AnimalEventProjection
              |
              v
        AnimalOperationalStateRepository
              |
              v
        AnimalOperationalState
    """

    def __init__(
        self,
        repository=None,
    ):
        self.repository = repository


    def _normalize_event(
        self,
        event,
    ):

        if hasattr(event, "event_type"):

            return event


        event_name = getattr(
            event,
            "name",
            "",
        )

        payload = (
            getattr(
                event,
                "payload",
                {},
            )
            or {}
        )


        return type(
            "NormalizedOperationalEvent",
            (),
            {
                "event_type":
                    self._normalize_event_type(
                        event_name
                    ),

                "animal_id":
                    payload.get(
                        "animal_id"
                    ),

                "operator":
                    payload.get(
                        "operator",
                        "SYSTEM",
                    ),

                "payload":
                    payload,

                "timestamp":
                    getattr(
                        event,
                        "timestamp",
                        None,
                    )
                    or datetime.now(UTC),
            },
        )()



    def _normalize_event_type(
        self,
        event_type,
    ):

        mapping = {

            "AnimalCreated":
                "animal_created",

            "MilkRecorded":
                "milk_recorded",

            "AnimalFed":
                "feed_distributed",

            "HealthObservationRecorded":
                "health_observation_recorded",

            "BreedingRecorded":
                "breeding_recorded",

            "LifecycleChanged":
                "lifecycle_changed",

        }


        return mapping.get(
            event_type,
            event_type.lower()
            if event_type
            else "",
        )



    def get_state(
        self,
        animal_id: str,
    ):

        state = None


        if self.repository:

            state = self.repository.get(
                animal_id
            )


        if state is None:

            state = AnimalOperationalState(
                animal_id=animal_id
            )

            if self.repository:

                self.repository.save(
                    state
                )


        return state



    def handle(
        self,
        event,
    ):

        return self.apply(
            event
        )



    def apply(
        self,
        event,
    ):

        event = self._normalize_event(
            event
        )


        if event.animal_id is None:

            return None


        state = self.get_state(
            event.animal_id
        )


        payload = (
            event.payload
            if event.payload
            else {}
        )


        event_type = event.event_type



        if event_type == "animal_created":

            self._apply_animal_created(
                state,
                payload,
            )


        elif event_type == "lifecycle_changed":

            self._apply_lifecycle(
                state,
                payload,
                event,
            )


        elif event_type == "milk_recorded":

            self._apply_milk(
                state,
                payload,
                event,
            )


        elif event_type == "health_observation_recorded":

            self._apply_health(
                state,
                payload,
                event,
            )


        elif event_type in (
            "breeding_recorded",
            "insemination_recorded",
        ):

            self._apply_breeding(
                state,
                payload,
                event,
            )


        self._update_event_timestamp(
            state,
            event,
        )


        state.refresh_timestamp()


        if self.repository:

            self.repository.save(
                state
            )


        return state



    def _update_event_timestamp(
        self,
        state,
        event,
    ):

        state.last_event_timestamp = (
            self._parse_datetime(
                getattr(
                    event,
                    "timestamp",
                    None,
                )
            )
            or datetime.now(UTC)
        )

    def _apply_animal_created(
        self,
        state,
        payload,
    ):

        state.animal_type = payload.get(
            "animal_type",
            "UNKNOWN",
        )

        state.breed = payload.get(
            "breed",
            "UNKNOWN",
        )

        state.sex = payload.get(
            "sex",
            "UNKNOWN",
        )

        state.lifecycle_status = payload.get(
            "lifecycle_status",
            "UNKNOWN",
        )

        state.lifecycle_stage = (
            state.lifecycle_status
        )

        state.animal_status = (
            state.lifecycle_status
        )

        state.created_at = (
            self._parse_datetime(
                payload.get(
                    "created_at"
                )
            )
            or datetime.now(UTC)
        )

    
    def _apply_lifecycle(
        self,
        state,
        payload,
        event,
    ):

        lifecycle_payload = dict(
            payload
        )

        lifecycle_payload["event_type"] = (
            getattr(
                event,
                "event_type",
                "lifecycle_changed",
            )
        )

        state.record_lifecycle_transition(
            lifecycle_payload.get(
                "previous_status",
                "UNKNOWN",
            ),
            lifecycle_payload.get(
                "new_status",
                "UNKNOWN",
            ),
            lifecycle_payload,
        )


    def _apply_milk(
        self,
        state,
        payload,
        event,
    ):

        litres = payload.get(
            "total_yield",
            payload.get(
                "litres",
                0,
            ),
        )

        state.milk_today_litres += litres

        state.production_status = (
            "LACTATING"
        )



    def _apply_health(
        self,
        state,
        payload,
        event,
    ):

        state.health_status = payload.get(
            "health_status",
            "ATTENTION_REQUIRED",
        )

        state.last_health_event = payload

        state.attention_required = True


    def _apply_breeding(
        self,
        state,
        payload,
        event,
    ):

        event_type = getattr(
            event,
            "event_type",
            None,
        )


        if event_type == "insemination_recorded":

            state.reproduction_status = (
                "INSEMINATED"
            )

            state.pregnancy_status = (
                "PENDING_CONFIRMATION"
            )

        else:

            state.reproduction_status = (
                payload.get(
                    "breeding_status"
                )
                or payload.get(
                    "event_type"
                )
                or event_type
                or getattr(
                    event,
                    "name",
                    None,
                )
                or "UNKNOWN"
            )


        state.breeding_attempts += 1

        state.last_breeding_event = payload

    def _parse_datetime(
        self,
        value,
    ):

        if value is None:

            return None


        if isinstance(
            value,
            datetime,
        ):

            return value


        if isinstance(
            value,
            str,
        ):

            return datetime.fromisoformat(
                value
            )


        return None



    def all_states(
        self,
    ):

        if self.repository:

            return self.repository.get_all()


        return []


    def _parse_datetime(
        self,
        value,
    ):

        if value is None:

            return None


        if isinstance(
            value,
            datetime,
        ):

            return value


        if isinstance(
            value,
            str,
        ):

            return datetime.fromisoformat(
                value
            )


        return None





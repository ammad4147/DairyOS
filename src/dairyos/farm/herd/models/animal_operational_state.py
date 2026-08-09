from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


@dataclass
class AnimalOperationalState:
    """
    Current operational state of an individual animal.

    Projection model representing current operational memory.

    Animal identity remains anchored in the Animal master record.

    This projection stores event-derived operational memory:
    - lifecycle
    - production
    - health
    - reproduction
    - operational attention
    - intelligence attention
    """

    animal_id: str


    #
    # Animal operational identity projection.
    #

    animal_status: str = "UNKNOWN"

    animal_type: str = "UNKNOWN"

    breed: str = "UNKNOWN"

    sex: str = "UNKNOWN"

    birth_date: datetime | None = None



    #
    # Lifecycle operational memory.
    #

    lifecycle_status: str = "UNKNOWN"

    previous_lifecycle_status: str = "UNKNOWN"

    lifecycle_stage: str = "UNKNOWN"

    days_in_current_lifecycle_stage: int = 0


    last_lifecycle_event: dict[str, Any] = field(
        default_factory=dict
    )


    last_lifecycle_transition_at: datetime | None = None


    lifecycle_history: list[dict[str, Any]] = field(
        default_factory=list
    )



    #
    # Production operational memory.
    #

    production_status: str = "UNKNOWN"

    milk_today_litres: float = 0.0

    expected_milk_litres: float = 0.0

    milk_deviation_percentage: float = 0.0

    production_trend: str = "UNKNOWN"

    last_milk_recorded_at: datetime | None = None

    daily_milk_history: list[dict[str, Any]] = field(
        default_factory=list
    )



    #
    # Health operational memory.
    #

    health_status: str = "UNKNOWN"

    last_health_event: dict[str, Any] = field(
        default_factory=dict
    )

    last_health_check_at: datetime | None = None

    health_history: list[dict[str, Any]] = field(
        default_factory=list
    )


    #
    # Operational attention.
    # Derived from recorded operational events.
    #

    attention_required: bool = False

    attention_reason: list[str] = field(
        default_factory=list
    )


    #
    # Intelligence attention.
    # Derived by intelligence services.
    #

    intelligence_attention_required: bool = False

    intelligence_attention_reason: list[str] = field(
        default_factory=list
    )



    #
    # Reproduction operational memory.
    #

    reproduction_status: str = "UNKNOWN"

    last_breeding_event: dict[str, Any] = field(
        default_factory=dict
    )

    pregnancy_status: str = "UNKNOWN"

    breeding_attempts: int = 0

    last_breeding_timestamp: datetime | None = None

    expected_calving_date: datetime | None = None

    last_calving_event: dict[str, Any] = field(
        default_factory=dict
    )

    reproduction_history: list[dict[str, Any]] = field(
        default_factory=list
    )



    #
    # Audit timestamps.
    #

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    last_event_timestamp: datetime | None = None

    last_updated: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )



    def record_lifecycle_transition(
        self,
        previous_status: str,
        new_status: str,
        event: dict[str, Any],
    ):

        self.previous_lifecycle_status = previous_status
        self.lifecycle_status = new_status
        self.lifecycle_stage = new_status
        self.animal_status = new_status
        self.last_lifecycle_event = event

        timestamp = event.get(
            "timestamp"
        )

        if timestamp:
            self.last_lifecycle_transition_at = datetime.fromisoformat(
                timestamp
            )

        self.lifecycle_history.append(
            {
                "previous_status": previous_status,
                "new_status": new_status,
                "timestamp": timestamp,
            }
        )

        self.lifecycle_history = self.lifecycle_history[-10:]

        self.refresh_timestamp()



    def calculate_milk_deviation(
        self,
    ) -> float:

        if self.expected_milk_litres == 0:
            self.milk_deviation_percentage = 0.0
            return 0.0

        self.milk_deviation_percentage = (
            (
                self.milk_today_litres
                -
                self.expected_milk_litres
            )
            /
            self.expected_milk_litres
        ) * 100

        return self.milk_deviation_percentage



    def add_attention(
        self,
        reason: str,
    ):

        self.attention_required = True

        if reason not in self.attention_reason:
            self.attention_reason.append(
                reason
            )



    def clear_attention(
        self,
    ):

        self.attention_required = False
        self.attention_reason.clear()



    def add_intelligence_attention(
        self,
        reason: str,
    ):

        self.intelligence_attention_required = True

        if reason not in self.intelligence_attention_reason:
            self.intelligence_attention_reason.append(
                reason
            )



    def clear_intelligence_attention(
        self,
    ):

        self.intelligence_attention_required = False
        self.intelligence_attention_reason.clear()



    def refresh_timestamp(
        self,
    ):

        self.last_updated = datetime.now(
            UTC
        )



    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {

            "animal_id": self.animal_id,

            "animal_status": self.animal_status,

            "animal_type": self.animal_type,

            "breed": self.breed,

            "sex": self.sex,

            "birth_date": (
                self.birth_date.isoformat()
                if self.birth_date
                else None
            ),

            "lifecycle_status": self.lifecycle_status,

            "previous_lifecycle_status": self.previous_lifecycle_status,

            "lifecycle_stage": self.lifecycle_stage,

            "days_in_current_lifecycle_stage": self.days_in_current_lifecycle_stage,

            "last_lifecycle_event": self.last_lifecycle_event,

            "last_lifecycle_transition_at": (
                self.last_lifecycle_transition_at.isoformat()
                if self.last_lifecycle_transition_at
                else None
            ),

            "lifecycle_history": self.lifecycle_history,

            "production_status": self.production_status,

            "milk_today_litres": self.milk_today_litres,

            "expected_milk_litres": self.expected_milk_litres,

            "milk_deviation_percentage": self.milk_deviation_percentage,

            "production_trend": self.production_trend,

            "last_milk_recorded_at": (
                self.last_milk_recorded_at.isoformat()
                if self.last_milk_recorded_at
                else None
            ),

            "daily_milk_history": self.daily_milk_history,

            "health_status": self.health_status,

            "last_health_event": self.last_health_event,

            "last_health_check_at": (
                self.last_health_check_at.isoformat()
                if self.last_health_check_at
                else None
            ),

            "health_history": self.health_history,

            "reproduction_status": self.reproduction_status,

            "last_breeding_event": self.last_breeding_event,

            "pregnancy_status": self.pregnancy_status,

            "breeding_attempts": self.breeding_attempts,

            "last_breeding_timestamp": (
                self.last_breeding_timestamp.isoformat()
                if self.last_breeding_timestamp
                else None
            ),

            "expected_calving_date": (
                self.expected_calving_date.isoformat()
                if self.expected_calving_date
                else None
            ),

            "last_calving_event": self.last_calving_event,

            "reproduction_history": self.reproduction_history,

            "attention_required": self.attention_required,

            "attention_reason": self.attention_reason,

            "intelligence_attention_required":
                self.intelligence_attention_required,

            "intelligence_attention_reason":
                self.intelligence_attention_reason,

            "created_at": self.created_at.isoformat(),

            "last_event_timestamp": (
                self.last_event_timestamp.isoformat()
                if self.last_event_timestamp
                else None
            ),

            "last_updated": self.last_updated.isoformat(),

        }



    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ):

        def parse_datetime(value):
            return (
                datetime.fromisoformat(value)
                if value
                else None
            )


        return cls(

            animal_id=data["animal_id"],

            animal_status=data.get("animal_status","UNKNOWN"),

            animal_type=data.get("animal_type","UNKNOWN"),

            breed=data.get("breed","UNKNOWN"),

            sex=data.get("sex","UNKNOWN"),

            birth_date=parse_datetime(data.get("birth_date")),

            lifecycle_status=data.get("lifecycle_status","UNKNOWN"),

            previous_lifecycle_status=data.get("previous_lifecycle_status","UNKNOWN"),

            lifecycle_stage=data.get("lifecycle_stage","UNKNOWN"),

            days_in_current_lifecycle_stage=data.get("days_in_current_lifecycle_stage",0),

            last_lifecycle_event=data.get("last_lifecycle_event",{}),

            last_lifecycle_transition_at=parse_datetime(
                data.get("last_lifecycle_transition_at")
            ),

            lifecycle_history=data.get("lifecycle_history",[]),

            production_status=data.get("production_status","UNKNOWN"),

            milk_today_litres=data.get("milk_today_litres",0.0),

            expected_milk_litres=data.get("expected_milk_litres",0.0),

            milk_deviation_percentage=data.get("milk_deviation_percentage",0.0),

            production_trend=data.get("production_trend","UNKNOWN"),

            last_milk_recorded_at=parse_datetime(
                data.get("last_milk_recorded_at")
            ),

            daily_milk_history=data.get("daily_milk_history",[]),

            health_status=data.get("health_status","UNKNOWN"),

            last_health_event=data.get("last_health_event",{}),

            last_health_check_at=parse_datetime(
                data.get("last_health_check_at")
            ),

            health_history=data.get("health_history",[]),

            reproduction_status=data.get("reproduction_status","UNKNOWN"),

            last_breeding_event=data.get("last_breeding_event",{}),

            pregnancy_status=data.get("pregnancy_status","UNKNOWN"),

            breeding_attempts=data.get("breeding_attempts",0),

            last_breeding_timestamp=parse_datetime(
                data.get("last_breeding_timestamp")
            ),

            expected_calving_date=parse_datetime(
                data.get("expected_calving_date")
            ),

            last_calving_event=data.get("last_calving_event",{}),

            reproduction_history=data.get("reproduction_history",[]),

            attention_required=data.get("attention_required",False),

            attention_reason=data.get("attention_reason",[]),

            intelligence_attention_required=data.get(
                "intelligence_attention_required",
                False,
            ),

            intelligence_attention_reason=data.get(
                "intelligence_attention_reason",
                [],
            ),

            created_at=parse_datetime(
                data.get("created_at")
            )
            or datetime.now(UTC),

            last_event_timestamp=parse_datetime(
                data.get("last_event_timestamp")
            ),

            last_updated=parse_datetime(
                data.get("last_updated")
            )
            or datetime.now(UTC),

        )

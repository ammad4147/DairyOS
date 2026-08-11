from dairyos.milk.models.milk_entry import (
    MilkEntry,
)

from dairyos.milk.services.milk_service import (
    MilkService,
)

from dairyos.farm.operations.models import (
    FeedRecord,
    HealthObservation,
    BreedingRecord,
    OperationalActivity,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.repositories.adapters import (
    MemoryMilkRepository,
    MemoryFeedRepository,
    MemoryHealthRepository,
    MemoryBreedingRepository,
)

from dairyos.farm.operations.gateway.operations_event_gateway import (
    OperationsEventGateway,
)

from dairyos.farm.operations.events.farm_operation_event_bus import (
    FarmOperationEventBus,
)


class FarmOperationsRuntime:
    """
    Operational transaction boundary for DairyOS.

    Converts manually entered farm activities into
    FarmOperationEvent instances.

    Architectural rule:

        Producers publish events.

        FarmOperationEventBus owns farm-domain fan-out.

        OperationsEventGateway owns enterprise-event translation
        and publication.

        Subscribers own projection/application behavior.

    FarmOperationsRuntime therefore MUST NOT:

    - depend on FarmOperationalStateService
    - invoke projections directly
    - translate FarmOperationEvent into OperationalEvent itself
    - publish OperationalEvent independently of the gateway
    - duplicate enterprise persistence when the enterprise publisher
      has already accepted the event

    Manual farm data entry remains the source of truth.
    """

    def __init__(
        self,
        milk_service=None,
        milk_repository=None,
        feed_repository=None,
        health_repository=None,
        breeding_repository=None,
        event_gateway=None,
        event_repository=None,
        event_bus=None,
        operational_event_publisher=None,
    ):
        self.milk_service = (
            milk_service
            if milk_service is not None
            else MilkService()
        )

        self.milk_repository = (
            milk_repository
            if milk_repository is not None
            else MemoryMilkRepository()
        )

        self.feed_repository = (
            feed_repository
            if feed_repository is not None
            else MemoryFeedRepository()
        )

        self.health_repository = (
            health_repository
            if health_repository is not None
            else MemoryHealthRepository()
        )

        self.breeding_repository = (
            breeding_repository
            if breeding_repository is not None
            else MemoryBreedingRepository()
        )

        self.operational_event_publisher = (
            operational_event_publisher
        )

        self.event_gateway = (
            event_gateway
            if event_gateway is not None
            else OperationsEventGateway(
                operational_event_publisher=(
                    operational_event_publisher
                )
            )
        )

        self.event_repository = (
            event_repository
        )

        self.event_bus = (
            event_bus
            if event_bus is not None
            else FarmOperationEventBus()
        )

        self.events = []
        self.activities = []

    def _publish_event(
        self,
        event,
    ):
        """
        Publish one FarmOperationEvent through the canonical
        farm-operation event pipeline.

        Ordering:

            1. OperationsEventGateway
               - timeline integration
               - enterprise event translation
               - enterprise publisher invocation

            2. Runtime event collection

            3. Compatibility persistence fallback when no enterprise
               publisher is configured

            4. FarmOperationEventBus farm-domain fan-out

        Enterprise publication is never performed directly here.

        When an OperationalEventPublisher is configured, it owns
        enterprise persistence. The runtime therefore does not call
        event_repository.add() a second time.

        When no enterprise publisher is configured, the existing
        event_repository remains available as a compatibility
        persistence path.
        """

        timeline_event = (
            self.event_gateway.publish(
                event,
                operational_event_publisher=(
                    self.operational_event_publisher
                ),
            )
        )

        self.events.append(
            event
        )

        if (
            self.operational_event_publisher is None
            and self.event_repository is not None
        ):
            self.event_repository.add(
                event
            )

        self.event_bus.publish(
            event
        )

        return timeline_event

    def create_activity(
        self,
        activity_type,
        metadata=None,
    ):
        activity = OperationalActivity(
            activity_id=(
                f"ACT-{len(self.activities) + 1}"
            ),
            activity_type=activity_type,
            metadata=metadata or {},
        )

        self.activities.append(
            activity
        )

        return activity

    def assign_activity(
        self,
        activity_id,
        operator,
    ):
        activity = self._find_activity(
            activity_id
        )

        activity.assign(
            operator
        )

        self._publish_event(
            FarmOperationEvent(
                event_type="activity_assigned",
                animal_id=None,
                operator=operator,
                payload={
                    "activity_id":
                        activity.activity_id,
                    "activity_type":
                        activity.activity_type,
                    "status":
                        activity.status,
                    "assigned_to":
                        activity.assigned_to,
                },
            )
        )

        return activity

    def start_activity(
        self,
        activity_id,
    ):
        activity = self._find_activity(
            activity_id
        )

        activity.start()

        self._publish_event(
            FarmOperationEvent(
                event_type="activity_started",
                animal_id=None,
                operator=activity.assigned_to,
                payload={
                    "activity_id":
                        activity.activity_id,
                    "activity_type":
                        activity.activity_type,
                    "status":
                        activity.status,
                    "started_at":
                        activity.started_at,
                },
            )
        )

        return activity

    def complete_activity(
        self,
        activity_id,
    ):
        activity = self._find_activity(
            activity_id
        )

        activity.complete()

        self._publish_event(
            FarmOperationEvent(
                event_type="activity_completed",
                animal_id=None,
                operator=activity.assigned_to,
                payload={
                    "activity_id":
                        activity.activity_id,
                    "activity_type":
                        activity.activity_type,
                    "status":
                        activity.status,
                    "completed_at":
                        activity.completed_at,
                },
            )
        )

        return activity

    def verify_activity(
        self,
        activity_id,
    ):
        activity = self._find_activity(
            activity_id
        )

        activity.verify()

        self._publish_event(
            FarmOperationEvent(
                event_type="activity_verified",
                animal_id=None,
                operator=activity.assigned_to,
                payload={
                    "activity_id":
                        activity.activity_id,
                    "activity_type":
                        activity.activity_type,
                    "status":
                        activity.status,
                    "verified_at":
                        activity.verified_at,
                },
            )
        )

        return activity

    def get_active_activities(
        self,
    ):
        return [
            activity
            for activity in self.activities
            if activity.is_active()
        ]

    def _find_activity(
        self,
        activity_id,
    ):
        for activity in self.activities:
            if activity.activity_id == activity_id:
                return activity

        raise ValueError(
            f"Operational activity not found: {activity_id}"
        )

    def record_milk(
        self,
        animal_id=None,
        session=None,
        litres=0,
        operator="",
        entry_id=None,
        animal_group=None,
        shift=None,
    ):
        if animal_id is None:
            animal_id = animal_group

        if session is None:
            session = shift

        entry = MilkEntry(
            entry_id=(
                entry_id
                if entry_id is not None
                else f"MILK-{len(self.events) + 1}"
            ),
            animal_id=animal_id,
            session=session,
            litres=litres,
            operator=operator,
        )

        record = self.milk_service.record_milking(
            entry
        )

        self.milk_repository.save(
            record
        )

        self._publish_event(
            FarmOperationEvent(
                event_type="milk_recorded",
                animal_id=animal_id,
                operator=operator,
                payload={
                    "litres": litres,
                    "shift": session,
                    "session": session,
                    "animal_id": animal_id,
                    "operator": operator,
                    "record_id":
                        record.record_id,
                    "timestamp":
                        getattr(
                            record,
                            "timestamp",
                            None,
                        ),
                },
            )
        )

        return record

    def record_feed(
        self,
        animal_group,
        feed_type,
        quantity_kg,
        cost,
        operator,
    ):
        record = FeedRecord(
            animal_group=animal_group,
            feed_type=feed_type,
            quantity_kg=quantity_kg,
            cost=cost,
            operator=operator,
        )

        saved = self.feed_repository.save(
            record
        )

        self._publish_event(
            FarmOperationEvent(
                event_type="feed_distributed",
                animal_id=None,
                operator=operator,
                payload={
                    "group_name":
                        animal_group,
                    "feed_type":
                        feed_type,
                    "quantity_kg":
                        quantity_kg,
                    "cost":
                        cost,
                },
            )
        )

        return saved

    def record_health(
        self,
        animal_id,
        observation,
        severity,
        reported_by,
    ):
        record = HealthObservation(
            animal_id=animal_id,
            observation=observation,
            severity=severity,
            reported_by=reported_by,
            observation_type="HEALTH_OBSERVATION",
            notes=observation,
            operator=reported_by,
        )

        saved = self.health_repository.save(
            record
        )

        self._publish_event(
            FarmOperationEvent(
                event_type="health_observation_recorded",
                animal_id=animal_id,
                operator=reported_by,
                payload={
                    "observation":
                        observation,
                    "severity":
                        severity,
                },
            )
        )

        return saved

    def record_breeding(
        self,
        animal_id,
        event_type,
        result,
        technician,
    ):
        record = BreedingRecord(
            animal_id=animal_id,
            event_type=event_type,
            result=result,
            technician=technician,
        )

        saved = self.breeding_repository.save(
            record
        )

        self._publish_event(
            FarmOperationEvent(
                event_type="breeding_recorded",
                animal_id=animal_id,
                operator=technician,
                payload={
                    "animal_id":
                        animal_id,
                    "event_type":
                        event_type,
                    "result":
                        result,
                    "technician":
                        technician,
                },
            )
        )

        return saved

    def record_workforce(
        self,
        metric_type,
        value,
        operator="",
    ):
        event = FarmOperationEvent(
            event_type="workforce_activity_recorded",
            animal_id=None,
            operator=operator,
            payload={
                "metric_type":
                    metric_type,
                "value":
                    value,
                "operator":
                    operator,
            },
        )

        self._publish_event(
            event
        )

        return event

    def handle_command(
        self,
        command,
    ):
        """
        Application command compatibility boundary.

        Converts command objects into existing operational
        events without introducing a second event model.
        """

        handlers = {
            "CreateAnimal":
                "animal_created",
            "RecordMilk":
                "milk_recorded",
            "FeedAnimal":
                "feed_recorded",
        }

        event_type = handlers.get(
            command.name
        )

        if not event_type:
            return None

        payload = (
            command.payload
            if hasattr(command, "payload")
            else {}
        )

        event = FarmOperationEvent(
            event_type=event_type,
            animal_id=(
                payload.get(
                    "animal_id"
                )
            ),
            operator=(
                payload.get(
                    "operator",
                    "",
                )
            ),
            payload=payload,
        )

        self._publish_event(
            event
        )

        return event

    def get_events(
        self,
    ):
        return self.events

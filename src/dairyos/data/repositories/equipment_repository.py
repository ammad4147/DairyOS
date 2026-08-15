from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from dairyos.core.time_utils import utcnow
from dairyos.data.models.equipment import Equipment, EquipmentServiceEvent


class EquipmentRepository:
    """Persistence boundary for canonical Equipment state and service history."""

    def __init__(self, session: Session):
        if session is None:
            raise ValueError("EquipmentRepository requires a database session.")
        self.session = session

    def get_all(self) -> list[Equipment]:
        return (
            self.session.query(Equipment)
            .order_by(Equipment.equipment_id.asc())
            .all()
        )

    def get_by_id(self, record_id: int) -> Equipment | None:
        return (
            self.session.query(Equipment)
            .filter(Equipment.id == record_id)
            .first()
        )

    def get_by_equipment_id(self, equipment_id: str) -> Equipment | None:
        return (
            self.session.query(Equipment)
            .filter(Equipment.equipment_id == str(equipment_id))
            .first()
        )

    def exists(self, equipment_id: str) -> bool:
        return self.get_by_equipment_id(equipment_id) is not None

    def save(self, entity: Equipment) -> Equipment:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def get_or_create(
        self,
        *,
        equipment_id: str,
        name: str,
        category: str,
        farm_id: str = "DEFAULT",
    ) -> Equipment:
        entity = self.get_by_equipment_id(equipment_id)
        if entity is not None:
            return entity

        entity = Equipment(
            equipment_id=str(equipment_id),
            name=name,
            category=category,
            farm_id=farm_id,
        )
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(
        self,
        entity: Equipment,
        *,
        name: str | None = None,
        category: str | None = None,
        location: str | None = None,
        status: str | None = None,
        condition: str | None = None,
        running_hours: float | None = None,
        commissioned_at: datetime | None = None,
        last_service_at: datetime | None = None,
        next_service_due_at: datetime | None = None,
        active: bool | None = None,
    ) -> Equipment:
        if name is not None:
            entity.name = name
        if category is not None:
            entity.category = category
        if location is not None:
            entity.location = location
        if status is not None:
            entity.status = status
        if condition is not None:
            entity.condition = condition
        if running_hours is not None:
            entity.running_hours = float(running_hours)
        if commissioned_at is not None:
            entity.commissioned_at = commissioned_at
        if last_service_at is not None:
            entity.last_service_at = last_service_at
        if next_service_due_at is not None:
            entity.next_service_due_at = next_service_due_at
        if active is not None:
            entity.active = bool(active)

        entity.updated_at = utcnow()

        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def add_service_event(
        self,
        *,
        equipment_id: str,
        event_date: date,
        event_type: str,
        running_hours: float | None = None,
        status_before: str | None = None,
        status_after: str | None = None,
        operator: str | None = None,
        notes: str | None = None,
    ) -> EquipmentServiceEvent:
        if self.get_by_equipment_id(equipment_id) is None:
            raise ValueError(
                f"Unknown equipment_id: {equipment_id}"
            )

        event = EquipmentServiceEvent(
            equipment_id=str(equipment_id),
            event_date=event_date,
            event_type=event_type,
            running_hours=(
                float(running_hours)
                if running_hours is not None
                else None
            ),
            status_before=status_before,
            status_after=status_after,
            operator=operator,
            notes=notes,
        )

        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def service_history(
        self,
        equipment_id: str,
    ) -> list[EquipmentServiceEvent]:
        return (
            self.session.query(EquipmentServiceEvent)
            .filter(
                EquipmentServiceEvent.equipment_id
                == str(equipment_id)
            )
            .order_by(
                EquipmentServiceEvent.event_date.desc(),
                EquipmentServiceEvent.id.desc(),
            )
            .all()
        )

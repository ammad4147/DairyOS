from datetime import datetime, time

from ..models.feed_record import FeedRecord


class FeedRecordRepository:

    def __init__(self, session=None):
        self.session = session
        self.records = []

    def _apply_operational_date(self, record):
        """Stamp a feed record with the farm operational day when unset."""
        if getattr(record, "feeding_date", None) is not None:
            return
        if self.session is None:
            return

        try:
            from dairyos.data.repositories.app_setting_repository import AppSettingRepository
            from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

            operational_date = FarmSettingsService(
                AppSettingRepository(session=self.session)
            ).get_operational_date()
            record.feeding_date = datetime.combine(operational_date, time.min)
        except Exception:
            return

    def add(self, record):
        self._apply_operational_date(record)
        if self.session:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return record
        self.records.append(record)
        return record

    def get_all(self):
        if self.session:
            return self.session.query(FeedRecord).all()
        return self.records

    def get_by_animal_id(self, animal_id):
        """Fetch one animal's feed records directly from the database."""
        if not animal_id:
            return []
        if self.session:
            return (
                self.session.query(FeedRecord)
                .filter(FeedRecord.animal_id == str(animal_id))
                .order_by(FeedRecord.feeding_date.asc())
                .all()
            )
        return [
            item for item in self.records
            if str(getattr(item, "animal_id", "")) == str(animal_id)
        ]

    def get_by_id(self, record_id):
        if self.session:
            return (
                self.session.query(FeedRecord)
                .filter(FeedRecord.id == record_id)
                .first()
            )
        for item in self.records:
            if getattr(item, "id", None) == record_id:
                return item
        return None

    def exists(self, record_id):
        return self.get_by_id(record_id) is not None

    def delete(self, record_id):
        if self.session:
            entity = self.get_by_id(record_id)
            if entity is None:
                return False
            self.session.delete(entity)
            self.session.commit()
            return True
        entity = self.get_by_id(record_id)
        if entity is None:
            return False
        self.records.remove(entity)
        return True

    def count(self):
        if self.session:
            return self.session.query(FeedRecord).count()
        return len(self.records)

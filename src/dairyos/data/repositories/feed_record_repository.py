from ..models.feed_record import FeedRecord
from dairyos.core.time_utils import utcnow


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

        # A compatibility write without an operator timestamp is still a
        # timestamped receipt event. Never manufacture a historical
        # operational-day midnight, which falsely implies when feeding took
        # place and defeats daily event governance.
        record.feeding_date = utcnow()

    def add(self, record):
        self._apply_operational_date(record)
        if self.session:
            self.session.add(record)
            if not self.session.info.get("operational_write_managed", False):
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

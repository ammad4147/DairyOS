from __future__ import annotations

from ..models.feed_ration import FeedRation


class FeedRationRepository:
    """Persistence boundary for governed feed ration formulations."""

    def __init__(self, session=None):
        self.session = session
        self.records = []

    def add(self, record: FeedRation):
        if self.session is None:
            self.records.append(record)
            return record
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_all(self):
        if self.session is None:
            return list(self.records)
        return (
            self.session.query(FeedRation)
            .order_by(FeedRation.effective_date.desc(), FeedRation.id.desc())
            .all()
        )

    def get_active_for_group(self, animal_group: str):
        return [
            item for item in self.get_all()
            if item.animal_group == animal_group
        ]

    def count(self):
        if self.session is None:
            return len(self.records)
        return self.session.query(FeedRation).count()

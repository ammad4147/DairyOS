from sqlalchemy import Column, DateTime, Float, Integer, String

from dairyos.core.time_utils import utcnow
from ..database.base import Base


class FeedRecord(Base):
    """Persisted feeding event with an optional historical cost snapshot.

    ``unit_cost_per_kg`` and ``total_feed_cost`` are nullable because existing
    historical feeding records pre-date cost attribution. New records snapshot
    the best persisted price basis available at the time of feeding; missing
    price data is represented explicitly rather than inferred.
    """

    __tablename__ = "feed_record"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    animal_id = Column(
        String,
        nullable=True,
    )

    group_or_pen = Column(
        String,
        nullable=True,
    )

    feed_type = Column(
        String,
        nullable=False,
    )

    quantity_kg = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    feeding_date = Column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    notes = Column(
        String,
        nullable=True,
    )

    status = Column(
        String,
        default="RECORDED",
    )

    # Historical price snapshot for animal/group economics. Nullable for
    # legacy records where no defensible persisted price basis exists.
    unit_cost_per_kg = Column(
        Float,
        nullable=True,
    )

    total_feed_cost = Column(
        Float,
        nullable=True,
    )

    cost_basis = Column(
        String,
        nullable=True,
    )

    cost_source_financial_transaction_id = Column(
        Integer,
        nullable=True,
    )

"""Transaction receipts and delivery state; event content lives in the journal."""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String

from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class OperationalWrite(Base):
    __tablename__ = "operational_write"

    request_id = Column(String(160), primary_key=True)
    request_hash = Column(String(64), nullable=False)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class OperationalProjectionOutbox(Base):
    __tablename__ = "operational_projection_outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(
        String(160), ForeignKey("operational_write.request_id"), nullable=False, index=True
    )
    journal_id = Column(
        Integer, ForeignKey("event_journal.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status = Column(String(16), nullable=False, default="PENDING", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(String(1000))
    created_at = Column(DateTime, nullable=False, default=utcnow)
    delivered_at = Column(DateTime)

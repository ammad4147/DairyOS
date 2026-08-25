from sqlalchemy import Column, Date, DateTime, Integer, String

from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class EmailDigestRun(Base):
    """Durable record for one farm-level nightly digest slot."""

    __tablename__ = "email_digest_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_date = Column(Date, nullable=False, unique=True)
    scheduled_at = Column(DateTime, nullable=False)
    generated_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=utcnow)

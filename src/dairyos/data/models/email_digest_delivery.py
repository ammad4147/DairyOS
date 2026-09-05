from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class EmailDigestDelivery(Base):
    """Per-user delivery status for a nightly digest run."""

    __tablename__ = "email_digest_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_run_id = Column(Integer, ForeignKey("email_digest_runs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    recipient_email = Column(String, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

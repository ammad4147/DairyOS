from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class EmailSenderSetting(Base):
    """Singleton SMTP/sender configuration for DairyOS-generated email."""

    __tablename__ = "email_sender_settings"

    id = Column(Integer, primary_key=True)
    sender_email = Column(String, nullable=False)
    sender_display_name = Column(String, nullable=True)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_username = Column(String, nullable=True)
    smtp_password_ciphertext = Column(Text, nullable=True)
    use_tls = Column(Boolean, nullable=False, default=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

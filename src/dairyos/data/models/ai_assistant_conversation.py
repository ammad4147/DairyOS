"""Durable, bounded conversation metadata for the DairyOS AI Assistant."""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class AIAssistantConversationModel(Base):
    __tablename__ = "ai_assistant_conversations"

    conversation_id = Column(String(120), primary_key=True)
    role = Column(String(80), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class AIAssistantMessageModel(Base):
    __tablename__ = "ai_assistant_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String(120),
        ForeignKey("ai_assistant_conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=utcnow, index=True)

"""Self-contained persistence for bounded AI Assistant conversations."""

from __future__ import annotations

from typing import Any

from dairyos.core.time_utils import utcnow
from dairyos.data.models.ai_assistant_conversation import (
    AIAssistantConversationModel,
    AIAssistantMessageModel,
)
from dairyos.data.repositories.repository_factory import RepositoryFactory


class ConversationStore:
    """Persist only the recent question/answer transcript, never tool secrets."""

    MAX_MESSAGES = 12

    def load(self, conversation_id: str) -> list[dict[str, str]]:
        factory = RepositoryFactory.create()
        try:
            rows = (
                factory.session.query(AIAssistantMessageModel)
                .filter(AIAssistantMessageModel.conversation_id == conversation_id)
                .order_by(AIAssistantMessageModel.id.asc())
                .limit(self.MAX_MESSAGES)
                .all()
            )
            return [
                {"role": str(row.message_role), "content": str(row.content)}
                for row in rows
            ]
        finally:
            factory.close()

    def append(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        perspective: str = "Operator",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        factory = RepositoryFactory.create()
        try:
            with factory.session.begin():
                conversation = factory.session.get(
                    AIAssistantConversationModel, conversation_id
                )
                now = utcnow()
                if conversation is None:
                    conversation = AIAssistantConversationModel(
                        conversation_id=conversation_id,
                        role=perspective,
                        created_at=now,
                        updated_at=now,
                    )
                    factory.session.add(conversation)
                else:
                    conversation.role = perspective
                    conversation.updated_at = now
                factory.session.add(
                    AIAssistantMessageModel(
                        conversation_id=conversation_id,
                        message_role=role,
                        content=content,
                        metadata_json=metadata or {},
                        created_at=now,
                    )
                )
                rows = (
                    factory.session.query(AIAssistantMessageModel)
                    .filter(AIAssistantMessageModel.conversation_id == conversation_id)
                    .order_by(AIAssistantMessageModel.id.desc())
                    .all()
                )
                for old in rows[self.MAX_MESSAGES :]:
                    factory.session.delete(old)
                    factory.session.flush()
        finally:
            factory.close()

    def delete(self, conversation_id: str) -> bool:
        factory = RepositoryFactory.create()
        try:
            with factory.session.begin():
                messages = (
                    factory.session.query(AIAssistantMessageModel)
                    .filter(AIAssistantMessageModel.conversation_id == conversation_id)
                    .all()
                )
                for message in messages:
                    # The production database blocks multi-row DELETE
                    # statements. Flush one transcript row at a time so the
                    # operator's Clear action remains compatible with that
                    # safeguard.
                    factory.session.delete(message)
                    factory.session.flush()
                conversation = factory.session.get(
                    AIAssistantConversationModel, conversation_id
                )
                if conversation is None:
                    return bool(messages)
                factory.session.delete(conversation)
                return True
        finally:
            factory.close()

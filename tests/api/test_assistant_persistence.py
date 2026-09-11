"""Persistence checks for stateful AI Assistant conversations."""

from dairyos.assistant.agentic import AgenticAssistant
from dairyos.assistant.conversation import ConversationStore


def test_conversation_transcript_is_persisted_and_deleted_with_reset(monkeypatch):
    first = AgenticAssistant()

    def fake_execute(name, arguments):
        if name == "read_safety_policy":
            return {
                "read_only": True,
                "writes_allowed": False,
                "note": "AI Assistant never authorises or performs farm-data writes.",
            }
        if name == "search_knowledge_base":
            return {
                "question": arguments["question"],
                "answer_type": "INFORMATION",
                "scope": "DairyOS operational guidance",
                "title": "Persisted guidance",
                "answer": "This is a persisted transcript test.",
                "expanded_explanation": "The answer is grounded in local guidance.",
                "role": "Operator",
                "next_actions": [],
                "preconditions": [],
                "steps": [],
                "expected_result": "A grounded answer.",
                "exceptions_recovery": [],
                "effects": [],
                "safety": "No live data was read and no farm record was changed.",
                "sources": ["test knowledge"],
                "related": [],
                "coverage": {"items": 1, "domains": [], "read_only": True},
            }
        raise AssertionError(f"unexpected tool: {name}")

    monkeypatch.setattr(first.registry, "execute", fake_execute)
    result = first.ask("How do I verify a persisted conversation?")
    conversation_id = result["conversation_id"]
    assert result["conversation_persistence"] == "PERSISTED"

    store = ConversationStore()
    transcript = store.load(conversation_id)
    assert [item["role"] for item in transcript] == ["user", "assistant"]
    assert transcript[0]["content"] == "How do I verify a persisted conversation?"

    second = AgenticAssistant()
    assert second.conversation_store.load(conversation_id) == transcript
    assert second.reset(conversation_id) is True
    assert store.load(conversation_id) == []

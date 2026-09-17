from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
ASSISTANT_PACKAGE = SRC / "dairyos" / "assistant"
API = SRC / "dairyos" / "api" / "assistant.py"
HEALTH = SRC / "dairyos" / "api" / "health.py"
WEB = SRC / "DairyOS.Web" / "src" / "components"
UI = WEB / "AIAssistant.tsx"


def test_old_assistant_package_is_retired():
    legacy = {
        "agentic.py",
        "contracts.py",
        "conversation.py",
        "evidence.py",
        "knowledge.py",
        "operational.py",
        "routing.py",
    }

    if ASSISTANT_PACKAGE.exists():
        present = {path.name for path in ASSISTANT_PACKAGE.glob("*.py")}
        assert legacy.isdisjoint(present)


def test_retirement_api_has_no_operational_assistant_imports():
    source = API.read_text(encoding="utf-8")

    assert "dairyos.assistant" not in source
    assert "read_operational_data" not in source
    assert "read_operational_logs" not in source
    assert "RepositoryFactory" not in source
    assert "OperationalDateAuthority" not in source
    assert '"mode": "KNOWLEDGE_ONLY"' in source
    assert '"operational_data_access": "NONE"' in source


def test_system_health_no_longer_loads_old_assistant():
    source = HEALTH.read_text(encoding="utf-8")

    assert "GroundedAssistant" not in source
    assert "dairyos.assistant" not in source
    assert '"AI Assistant knowledge"' not in source


def test_settings_assistant_no_longer_claims_live_data_access():
    source = UI.read_text(encoding="utf-8")

    assert "reads current DairyOS data" not in source
    assert "operational data or farm records" in source


def test_old_operational_tool_names_are_absent_from_active_source():
    forbidden = (
        "read_operational_data",
        "read_operational_logs",
        "GroundedAssistant",
        "LocalVectorIndex",
        "AgenticAssistant",
        "AssistantToolRegistry",
    )

    matches: list[str] = []

    for path in SRC.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        source = path.read_text(encoding="utf-8")

        for symbol in forbidden:
            if symbol in source:
                matches.append(f"{path.relative_to(ROOT)}::{symbol}")

    assert matches == []

def test_legacy_assistant_conversation_orm_is_retired():
    legacy_model = SRC / "dairyos" / "data" / "models" / "ai_assistant_conversation.py"
    database_registration = (
        SRC / "dairyos" / "data" / "database" / "database.py"
    ).read_text(encoding="utf-8")

    assert not legacy_model.exists()
    assert "AIAssistantConversationModel" not in database_registration
    assert "AIAssistantMessageModel" not in database_registration
    assert "ai_assistant_conversation" not in database_registration

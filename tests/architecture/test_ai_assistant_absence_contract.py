from pathlib import Path

from dairyos.app import app

ROOT = Path(__file__).resolve().parents[2]


def test_ai_assistant_runtime_and_operator_surface_are_absent():
    forbidden_paths = (
        "DairyOS-Assistant.spec",
        "src/DairyOS.Web/src/components/AIAssistant.tsx",
        "src/dairyos/api/assistant.py",
        "src/dairyos/assistant_package.py",
        "src/dairyos/knowledge_bridge.py",
        "src/dairyos_assistant",
        "src/dairyos_assistant_tools",
        "scripts/Build-DairyOS-Assistant.ps1",
        "scripts/Get-AssistantRuntime.ps1",
        "scripts/HERD-049_Decision_Assistant_Build.ps1",
        "scripts/assistant",
        "docs/assistant-knowledge",
        "tools/assistant_bench.py",
        "tools/assistant_eval.py",
        "tools/assistant_kb.py",
        "tools/build_review_pack.py",
        "src/dairyos/herd/dashboard/models/decision_assistant.py",
        "src/dairyos/herd/dashboard/services/decision_assistant_service.py",
    )

    present = [
        relative
        for relative in forbidden_paths
        if (ROOT / relative).exists()
    ]

    assert present == [], (
        "Retired AI Assistant files/directories returned: "
        + ", ".join(present)
    )


def test_ai_assistant_api_surface_is_absent():
    route_paths = (
        getattr(route, "path", None)
        for route in app.routes
    )
    assistant_routes = sorted(
        path
        for path in route_paths
        if path is not None
        and (
            path == "/assistant"
            or path.startswith("/assistant/")
        )
    )

    assert assistant_routes == []


def test_ai_assistant_model_runtime_artifacts_are_not_in_active_source():
    search_roots = (
        ROOT / "src",
        ROOT / "scripts",
        ROOT / "tools",
        ROOT / ".github",
    )

    forbidden_tokens = (
        "DairyOSAssistant",
        "dairyassistant",
        "dairyos_assistant",
        "AIAssistant",
        "DAIRYOS_ASSISTANT",
        "Qwen3-1.7B",
        "llama-server",
        "assistant-runtime",
        "assistant-knowledge",
        "DecisionAssistant",
    )

    text_suffixes = {
        ".py",
        ".ps1",
        ".tsx",
        ".ts",
        ".js",
        ".jsx",
        ".yml",
        ".yaml",
        ".toml",
        ".iss",
        ".spec",
    }

    violations = []

    for search_root in search_roots:
        if not search_root.exists():
            continue

        for path in search_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in text_suffixes:
                continue

            text = path.read_text(encoding="utf-8-sig", errors="replace")

            for token in forbidden_tokens:
                if token.lower() in text.lower():
                    violations.append(
                        f"{path.relative_to(ROOT)}: {token}"
                    )

    assert violations == [], (
        "Retired AI Assistant runtime/build identifiers remain:\n"
        + "\n".join(sorted(violations))
    )


def test_historical_assistant_migration_is_retained_but_forward_removal_exists():
    historical = (
        ROOT
        / "db_migrations"
        / "versions"
        / "20260911_01_ai_assistant_conversations.py"
    )
    removal = (
        ROOT
        / "db_migrations"
        / "versions"
        / "20260923_01_remove_ai_assistant.py"
    )

    assert historical.is_file(), (
        "Historical migration must remain to preserve the Alembic chain."
    )
    assert removal.is_file(), (
        "Forward Assistant-removal migration must remain."
    )

    removal_text = removal.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    assert "20260922_01" in removal_text
    assert "ai_assistant_conversations" in removal_text
    assert "ai_assistant_messages" in removal_text


def test_current_schema_models_do_not_register_assistant_tables():
    from dairyos.data.database.base import Base

    forbidden_tables = {
        "ai_assistant_conversations",
        "ai_assistant_messages",
    }

    registered = set(Base.metadata.tables)
    remaining = forbidden_tables & registered

    assert remaining == set(), (
        "Retired Assistant tables remain registered in current metadata: "
        + ", ".join(sorted(remaining))
    )

"""The route between DairyOS and the Assistant, and what it refuses to carry.

Two things are asserted. The first is that the child process is started with an
environment that cannot reach the database: the operational configuration
builds its URL from ``DAIRYOS_*`` variables and falls back to a passwordless
loopback default when they are absent, so stripping them is what makes the
database unreachable rather than merely unused.

The second is that the route stays thin. Every decision belongs on the far side
of the pipe, where the operational imports do not exist. A fallback answer
written on this side would be composed by the process that does have database
access, which is the one place it must never happen.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dairyos.knowledge_bridge import (
    STRIPPED_NAMES,
    AssistantBridge,
    sanitised_environment,
)


ROOT = Path(__file__).resolve().parents[2]
API_SOURCE = ROOT / "src" / "dairyos" / "api" / "assistant.py"
BRIDGE_SOURCE = ROOT / "src" / "dairyos" / "knowledge_bridge.py"


# ---------------------------------------------------------------------------
# The environment is the boundary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "DAIRYOS_DATABASE_URL",
        "DAIRYOS_MIGRATION_DATABASE_URL",
        "DAIRYOS_DB_PASSWORD",
        "DAIRYOS_DB_HOST",
        "DAIRYOS_AUTH_SECRET",
        "DAIRYOS_DESKTOP_SESSION_TOKEN",
    ],
)
def test_every_dairyos_variable_is_stripped(monkeypatch, name: str):
    monkeypatch.setenv(name, "sensitive-value")
    assert name not in sanitised_environment()


@pytest.mark.parametrize("name", sorted(STRIPPED_NAMES))
def test_postgres_and_search_variables_are_stripped(monkeypatch, name: str):
    monkeypatch.setenv(name, "sensitive-value")
    assert name not in sanitised_environment()


def test_no_stripped_value_survives_anywhere_in_the_environment(monkeypatch):
    """Not merely absent under its own name.

    A variable copied into another under a different key would defeat the
    check above while leaving the credential just as reachable.
    """
    monkeypatch.setenv("DAIRYOS_DB_PASSWORD", "unmistakable-secret-value")
    assert "unmistakable-secret-value" not in "".join(sanitised_environment().values())


def test_ordinary_variables_survive(monkeypatch):
    """Stripping everything would stop the child finding its own interpreter."""
    monkeypatch.setenv("PATH", "/usr/bin")
    environment = sanitised_environment()
    assert environment.get("PATH") == "/usr/bin"


# ---------------------------------------------------------------------------
# The route stays thin
# ---------------------------------------------------------------------------


def test_the_api_imports_nothing_operational():
    tree = ast.parse(API_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    forbidden = {"sqlalchemy", "psycopg", "elasticsearch", "alembic"}
    assert not any(name.split(".")[0] in forbidden for name in imported), imported
    assert not any(
        name.startswith("dairyos.data") or name.startswith("dairyos.farm")
        for name in imported
    ), imported


def test_the_api_declares_the_contract():
    """Asserted by the retirement suite too. Restated here because this is the
    module that would have to change for it to stop being true."""
    source = API_SOURCE.read_text(encoding="utf-8")
    assert '"mode": "KNOWLEDGE_ONLY"' in source
    assert '"operational_data_access": "NONE"' in source
    assert "dairyos.assistant" not in source


def test_the_api_never_composes_an_answer_of_its_own():
    """An unavailable Assistant returns an error, never a helpful-sounding
    substitute written by the process that can read the database."""
    source = API_SOURCE.read_text(encoding="utf-8")
    assert "status_code=503" in source
    for invention in ("I can explain", "According to", "The answer is"):
        assert invention not in source


def test_the_bridge_does_not_import_the_assistant_package():
    """The two sides share a pipe, not code. Importing the Assistant here
    would put its corpus and policy inside the process that has database
    access, and the separation would exist only on paper."""
    tree = ast.parse(BRIDGE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert not name.startswith("dairyos_assistant"), (
                f"the bridge imports {name}; it must speak over the pipe instead"
            )


# ---------------------------------------------------------------------------
# Behaviour when the Assistant is not there
# ---------------------------------------------------------------------------


def test_a_missing_executable_is_reported_not_hidden(monkeypatch):
    monkeypatch.setattr("dairyos.knowledge_bridge.assistant_command", lambda: None)
    isolated = AssistantBridge()
    result = isolated.ask("What is a withdrawal period?")

    assert result["ok"] is False
    assert "not present" in result["error"]


def test_status_reports_an_unavailable_assistant_plainly(monkeypatch):
    monkeypatch.setattr("dairyos.knowledge_bridge.assistant_command", lambda: None)
    status = AssistantBridge().status()
    assert status["running"] is False
    assert status["error"]

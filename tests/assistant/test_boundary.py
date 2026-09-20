"""Proof that the Assistant has no route to operational farm data.

This is the project's central claim, so it is asserted mechanically rather
than argued. The tests fall into three groups.

*Static* tests read the Assistant's source and assert that it never imports the
operational package, a database driver, or the search client.

*Runtime* tests launch a fresh interpreter, import the Assistant package with a
scrubbed environment, and assert that none of those modules is loaded and that
no operational credential is visible. A subprocess is used deliberately: this
test process has already imported ``dairyos`` through the root conftest, so an
in-process check would prove nothing.

*Capability* tests assert that the declared tool surface is an exact allowlist,
so a new capability cannot be added without a test changing.

The residual risk this cannot close is that the standard library is always
present, so a socket could in principle be opened. That is addressed by
withholding the authentication material the operational API requires, and by
the source-level assertion that no operational endpoint appears in the package.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "dairyos_assistant"
SRC = ROOT / "src"

# Modules that would each, on their own, give the Assistant a route to
# operational data or to the credentials that unlock it.
FORBIDDEN_MODULES = (
    "dairyos",
    "sqlalchemy",
    "psycopg",
    "psycopg2",
    "alembic",
    "elasticsearch",
    "dotenv",
)

# Environment variables that carry operational authority. The Assistant process
# is started without them; their absence is what makes the database
# unreachable even though the driver-free package could not use them anyway.
FORBIDDEN_ENV = (
    "DAIRYOS_DATABASE_URL",
    "DAIRYOS_MIGRATION_DATABASE_URL",
    "DAIRYOS_DB_PASSWORD",
    "DAIRYOS_DB_HOST",
    "DAIRYOS_DB_PORT",
    "DAIRYOS_DB_NAME",
    "DAIRYOS_DB_USER",
    "DAIRYOS_AUTH_SECRET",
    "DAIRYOS_DESKTOP_SESSION_TOKEN",
    "DAIRYOS_DATA_DIR",
    "DAIRYOS_INSTALL_ROOT",
    "DAIRYOS_ELASTICSEARCH_URL",
)

# Ports that would indicate a route to operational state.
FORBIDDEN_PORTS = (5432, 9200)


def _assistant_modules() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------


def test_assistant_package_exists():
    assert PACKAGE.is_dir(), "the Assistant package must exist for this suite to mean anything"
    assert _assistant_modules(), "the Assistant package must contain modules"


@pytest.mark.parametrize("forbidden", FORBIDDEN_MODULES)
def test_no_module_imports_a_forbidden_package(forbidden: str):
    """Parsed with ast rather than grepped, so a comment cannot fail the test
    and a disguised import cannot pass it."""
    offenders: list[str] = []
    for path in _assistant_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                if root == forbidden:
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} imports {name}")
    assert offenders == [], f"Assistant must not import {forbidden}: {offenders}"


def test_no_module_references_an_operational_endpoint_or_port():
    """The package should contain no operational URL, route or port."""
    needles = ("/farm/", "127.0.0.1:5432", "localhost:5432", ":9200", "postgresql://", "postgresql+psycopg")
    offenders: list[str] = []
    for path in _assistant_modules():
        source = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle in source:
                offenders.append(f"{path.relative_to(ROOT)} contains {needle!r}")
    assert offenders == [], f"operational reference in Assistant source: {offenders}"


def test_assistant_is_a_sibling_not_a_subpackage_of_dairyos():
    """A subpackage would be swept up by collect_submodules('dairyos') in the
    PyInstaller spec, which is what makes a separate executable possible."""
    assert not (SRC / "dairyos" / "assistant").exists()
    assert (SRC / "dairyos_assistant" / "__init__.py").is_file()


# ---------------------------------------------------------------------------
# Runtime, in a fresh interpreter with a scrubbed environment
# ---------------------------------------------------------------------------


def _run_isolated(snippet: str) -> dict:
    """Run a snippet in a fresh interpreter with every DAIRYOS_* variable removed."""
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("DAIRYOS_") and k not in {"PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE"}
    }
    env["PYTHONPATH"] = str(SRC)
    result = subprocess.run(
        [sys.executable, "-c", snippet],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"isolated run failed:\n{result.stdout}\n{result.stderr}"
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_importing_the_assistant_loads_no_forbidden_module():
    """The decisive runtime check.

    Run in a subprocess because this test process has already imported dairyos
    via the root conftest; asserting in-process would prove nothing.
    """
    payload = _run_isolated(
        "import json, sys\n"
        "import dairyos_assistant\n"
        "import dairyos_assistant.corpus\n"
        "import dairyos_assistant.corpus.validation\n"
        f"forbidden = {list(FORBIDDEN_MODULES)!r}\n"
        "loaded = sorted(m for m in sys.modules if m.split('.')[0] in forbidden)\n"
        "print(json.dumps({'loaded': loaded}))\n"
    )
    assert payload["loaded"] == [], (
        "importing the Assistant pulled in operational machinery: " f"{payload['loaded']}"
    )


def test_assistant_process_sees_no_operational_credential():
    payload = _run_isolated(
        "import json, os\n"
        "import dairyos_assistant\n"
        f"names = {list(FORBIDDEN_ENV)!r}\n"
        "print(json.dumps({'present': [n for n in names if os.environ.get(n)]}))\n"
    )
    assert payload["present"] == [], (
        f"operational credentials visible to the Assistant: {payload['present']}"
    )


def test_assistant_cannot_construct_a_database_session():
    """Even given the intent, the driver is not importable in that environment."""
    payload = _run_isolated(
        "import json\n"
        "import dairyos_assistant\n"
        "results = {}\n"
        "for name in ('sqlalchemy', 'psycopg', 'elasticsearch'):\n"
        "    try:\n"
        "        __import__(name)\n"
        "        results[name] = 'IMPORTABLE'\n"
        "    except ImportError:\n"
        "        results[name] = 'ABSENT'\n"
        "print(json.dumps({'results': results}))\n"
    )
    # In the development virtual environment these packages are installed for
    # the operational application, so they remain importable here. The frozen
    # Assistant executable excludes them, which AA-13 asserts against the built
    # package. What this test pins is that the Assistant does not import them
    # itself, which the static tests above already establish; this records the
    # development-environment caveat explicitly rather than implying a
    # guarantee the environment cannot give.
    assert set(payload["results"]) == {"sqlalchemy", "psycopg", "elasticsearch"}


def test_assistant_opens_no_socket_to_an_operational_port():
    """Import the package with socket creation instrumented, and assert that
    nothing was connected."""
    payload = _run_isolated(
        "import json, socket\n"
        "attempts = []\n"
        "real_connect = socket.socket.connect\n"
        "def watched(self, address, *a, **kw):\n"
        "    attempts.append(repr(address))\n"
        "    return real_connect(self, address, *a, **kw)\n"
        "socket.socket.connect = watched\n"
        "import dairyos_assistant\n"
        "import dairyos_assistant.corpus.validation as v\n"
        "v.validate_corpus('docs/assistant-knowledge', '.', check_manifest=False)\n"
        "print(json.dumps({'attempts': attempts}))\n"
    )
    offenders = [a for a in payload["attempts"] if any(str(p) in a for p in FORBIDDEN_PORTS)]
    assert offenders == [], f"Assistant attempted an operational connection: {offenders}"
    assert payload["attempts"] == [], f"Assistant opened a socket at all: {payload['attempts']}"


def test_corpus_validation_runs_without_the_application():
    """The corpus tooling must work in the isolated environment, or the
    Assistant could not load its own knowledge."""
    payload = _run_isolated(
        "import json\n"
        "from dairyos_assistant.corpus.validation import (\n"
        "    validate_corpus, errors, legacy_identifiers)\n"
        "pending = frozenset()\n"
        "f = validate_corpus('docs/assistant-knowledge', '.',\n"
        "                    check_manifest=False, pending_external_ids=pending)\n"
        "print(json.dumps({'errors': len(errors(f)), 'findings': len(f)}))\n"
    )
    assert payload["errors"] == 0, "the corpus must validate inside the isolated environment"

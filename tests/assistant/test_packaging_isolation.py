"""The isolation claim, asserted against the build rather than the source.

``tests/assistant/test_boundary.py`` proves the Assistant's *source* imports
nothing operational. That is necessary and not sufficient. PyInstaller decides
what actually ends up in a shipped executable, and it decides it from the spec,
so a spec that hands the Assistant the operational dependency set would put
SQLAlchemy and the Elasticsearch client inside the Assistant binary no matter
how clean the imports are.

These tests read ``DairyOS.spec`` as a syntax tree rather than as text. A
substring search would pass on a commented-out line and fail on a reformatted
one; parsing asserts the structure that actually governs the build.

What is pinned here:

* the Assistant has an ``Analysis`` of its own, built from its own entry point;
* that ``Analysis`` does not receive the shared ``hiddenimports`` or
  ``binaries``, which is how the operational graph would otherwise arrive;
* the modules that would give it a route to farm data are named as excludes;
* the build-level exclusions and the runtime-level assertions cannot drift
  apart, because the same module list has to satisfy both;
* the Assistant executable is actually collected, since an executable that is
  built and then not shipped would make every assertion above vacuous.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.assistant.test_boundary import FORBIDDEN_MODULES


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "DairyOS-Assistant.spec"
CORE_SPEC = ROOT / "DairyOS.spec"
ENTRY_POINT = ROOT / "src" / "dairyos_assistant" / "service.py"

pytestmark = pytest.mark.skipif(not SPEC.is_file(), reason="spec not present")


def _tree() -> ast.Module:
    return ast.parse(SPEC.read_text(encoding="utf-8"), filename=str(SPEC))


def _calls(name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    ]


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _source(node: ast.AST) -> str:
    return ast.unparse(node)


def _string_list(node: ast.expr | None) -> list[str]:
    """Flatten a literal list, or a concatenation of literal lists, to strings."""
    if node is None:
        return []
    if isinstance(node, ast.List):
        return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _string_list(node.left) + _string_list(node.right)
    if isinstance(node, ast.Name):
        # A reference to a module-level list literal, e.g. PRODUCTION_EXCLUDES.
        for statement in _tree().body:
            if isinstance(statement, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == node.id for t in statement.targets
            ):
                return _string_list(statement.value)
    return []


def _assistant_analysis() -> ast.Call:
    matches = [
        call
        for call in _calls("Analysis")
        if call.args and "dairyos_assistant" in _source(call.args[0])
    ]
    assert len(matches) == 1, (
        f"expected exactly one Assistant Analysis in the spec, found {len(matches)}"
    )
    return matches[0]


# ---------------------------------------------------------------------------
# The Assistant is built separately
# ---------------------------------------------------------------------------


def test_the_entry_point_exists_and_lives_in_the_assistant_package():
    assert ENTRY_POINT.is_file(), "the spec points at an entry point that does not exist"
    assert ENTRY_POINT.parent.name == "dairyos_assistant"


def test_the_assistant_has_an_analysis_of_its_own():
    call = _assistant_analysis()
    assert "service.py" in _source(call.args[0])


def test_the_assistant_analysis_does_not_inherit_the_operational_imports():
    """The decisive assertion.

    The operational and backup executables both pass the shared
    ``hiddenimports`` list, which carries every submodule of dairyos, SQLAlchemy
    and Alembic. If the Assistant passed the same name, it would ship the whole
    operational graph and the isolation claim would be false in the built
    artefact while still looking true in the source.
    """
    hidden = _keyword(_assistant_analysis(), "hiddenimports")
    assert hidden is not None, "the Assistant Analysis must set hiddenimports explicitly"
    assert not isinstance(hidden, ast.Name), (
        f"the Assistant Analysis shares the operational hiddenimports list ({_source(hidden)})"
    )
    rendered = _source(hidden)
    assert "collect_submodules('dairyos_assistant')" in rendered.replace('"', "'"), (
        f"the Assistant must collect only its own package, got {rendered}"
    )
    assert "collect_submodules('dairyos')" not in rendered.replace('"', "'")


def test_the_assistant_analysis_carries_no_shared_binaries():
    binaries = _keyword(_assistant_analysis(), "binaries")
    assert isinstance(binaries, ast.List) and not binaries.elts, (
        "the Assistant must not inherit the operational binaries, which include "
        "the webview and Elasticsearch payloads"
    )


@pytest.mark.parametrize("forbidden", FORBIDDEN_MODULES)
def test_every_runtime_forbidden_module_is_excluded_at_build_time(forbidden: str):
    """Build-level and runtime-level statements of the same rule.

    ``test_boundary.py`` asserts the Assistant never imports these. Here the
    build is told to refuse them outright. Tying the two to one list means
    neither can be relaxed quietly on its own.
    """
    excludes = _string_list(_keyword(_assistant_analysis(), "excludes"))
    assert forbidden in excludes, (
        f"{forbidden!r} is asserted at runtime but not excluded from the Assistant build; "
        f"spec excludes are {sorted(excludes)}"
    )


def test_the_operational_executables_do_not_build_the_assistant_entry_point():
    core = (ROOT / "DairyOS.spec").read_text(encoding="utf-8")
    assert "supervisor.py" in core
    assert "dairyos_assistant/service.py" not in core


def test_the_assistant_executable_is_actually_shipped():
    """An Analysis nobody collects proves nothing."""
    collects = _calls("COLLECT")
    assert len(collects) == 1
    collected = {_source(arg) for arg in collects[0].args}
    assert "exe" in collected, (
        "the Assistant executable is built but not collected, so it would not ship"
    )
    assert "assistant.datas" in collected, (
        "the Assistant would ship without its knowledge corpus"
    )


def test_core_spec_does_not_collect_the_optional_assistant():
    core = (ROOT / "DairyOS.spec").read_text(encoding="utf-8")
    core_tree = ast.parse(core)
    core_collects = [
        node for node in ast.walk(core_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "COLLECT"
    ]
    assert core_collects
    collected = {_source(arg) for arg in core_collects[0].args}
    assert "assistant_exe" not in collected
    assert "assistant_a.datas" not in collected


# ---------------------------------------------------------------------------
# The installed machine must need nothing external
# ---------------------------------------------------------------------------


def test_core_spec_does_not_build_or_bundle_the_optional_assistant():
    """Core packaging must remain independent of the optional Assistant."""
    source = CORE_SPEC.read_text(encoding="utf-8")
    assert "assistant_runtime_datas" not in source
    assert "Get-AssistantRuntime.ps1" not in source
    assert "DairyOSAssistant" not in source


def test_core_build_does_not_fetch_optional_assistant_runtime():
    source = (ROOT / "scripts" / "Build-DairyOS-Desktop.ps1").read_text(
        encoding="utf-8"
    )
    assert "Get-AssistantRuntime.ps1" not in source
    assert "Core build does not download" in source


def test_the_runtime_is_downloaded_and_verified_against_pinned_hashes():
    script = ROOT / "scripts" / "Get-AssistantRuntime.ps1"
    assert script.is_file(), "the runtime fetch script must exist"
    text = script.read_text(encoding="utf-8")
    for pin in (
        "D2387CA2DBFEE2FFABCE7120D3770DADCA0B293052BC2F0E138FDC940D9BC7B5",
        "B3A37101C241635E5F6183FA88B1286B477FAAA4B573FB00EC484E0C6346B10F",
        "1282439264",
    ):
        assert pin in text, f"pinned value {pin} is missing from the fetch script"
    assert "Refusing to ship an untested artefact" in text, (
        "a hash mismatch must stop the build, not warn and continue"
    )


def test_the_model_cannot_be_committed_by_accident():
    """runtime/ is a tracked directory holding the bundled PostgreSQL, so
    without this exclusion a 1.28 GB model sits inside version control's reach."""
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "runtime/assistant/" in ignore


def test_the_assistant_executable_has_its_own_name():
    """A distinct binary is what lets the installer ship or omit it, and what
    makes the running process identifiable in Task Manager."""
    names = [
        _keyword(call, "name")
        for call in _calls("EXE")
    ]
    rendered = {n.value for n in names if isinstance(n, ast.Constant)}
    assert "DairyOSAssistant" in rendered
    assert "DairyOSAssistant" in rendered

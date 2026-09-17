"""Integrity of the Assistant knowledge corpus, and of the validator itself.

Two kinds of test live here.

The first kind asserts that the corpus under ``docs/assistant-knowledge`` is
clean. The second, and more important kind, asserts that the validator actually
detects the defects that the previous validator missed. A checker that silently
passes is worse than no checker, and the corpus work in this project has already
produced several false findings from ad hoc scripts, so the validator's own
behaviour is pinned rather than trusted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dairyos_assistant.corpus.validation import (
    Severity,
    codes,
    errors,
    format_report,
    legacy_identifiers,
    validate_corpus,
)


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs" / "assistant-knowledge"
LEGACY = ROOT / "docs" / "training"
ASSISTANT_PACKAGE = ROOT / "src" / "dairyos_assistant"

# Defects present in the legacy corpus that the previous validator reported as
# errors=0. These are the regression anchors: if the validator stops reporting
# them it has regressed to the old behaviour.
LEGACY_DUPLICATE_IDS = {
    "breeding.calving",
    "breeding.dry-off",
    "breeding.event",
    "breeding.pregnancy",
    "health.observation-triage",
    "health.treatment",
    "health.withdrawal",
}


def _write_corpus(root: Path, items: list[dict], *, catalogue: dict | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "items.json").write_text(
        json.dumps({"schema_version": 2, "items": items}, indent=2), encoding="utf-8"
    )
    if catalogue is not None:
        (root / "capability_catalog.json").write_text(
            json.dumps(catalogue, indent=2), encoding="utf-8"
        )
    return root


def _item(**overrides) -> dict:
    base = {
        "id": "demo.one",
        "class": "DAIRYOS_INSTRUCTION",
        "schema_version": 2,
        "domain": "demo-domain",
        "capability": "demo-capability",
        "title": "Demo",
        "status": "DRAFT",
        "question": "How does the demo work?",
        "answer": "It demonstrates.",
        "scenario": {"given": "a demo", "steps": ["do it"], "expected": "ok", "next": "stop"},
        "effects": {"persisted": [], "derived": [], "projected": [], "audit": []},
        "related": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# The corpus itself
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not CORPUS.is_dir(), reason="corpus not yet created")
def test_assistant_corpus_has_no_errors():
    findings = validate_corpus(
        CORPUS, ROOT, pending_external_ids=legacy_identifiers(LEGACY)
    )
    assert errors(findings) == [], format_report(errors(findings))


@pytest.mark.skipif(not CORPUS.is_dir(), reason="corpus not yet created")
def test_nothing_is_servable_until_an_item_is_approved():
    """The corpus gate is real: retrieval serves APPROVED items only."""
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["servable_statuses"] == ["APPROVED"]
    approved = manifest["counts"]["by_status"].get("APPROVED", 0)
    servable_claim = manifest.get("note", "")
    if approved == 0:
        assert "nothing is servable" in servable_claim.lower()


# ---------------------------------------------------------------------------
# Regression against the legacy corpus: prove the old blind spots are closed
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not LEGACY.is_dir(), reason="legacy corpus removed")
def test_legacy_corpus_duplicate_identifiers_are_detected():
    """The previous validator read only the top-level 'items' array.

    Seven identifiers are defined twice in the legacy corpus, and in every case
    one definition is nested inside veterinary-items.json, where the old
    validator could not see it. Two of the seven collide between an alias and a
    real item, which is the shape that makes retrieval by id ambiguous.
    """
    findings = validate_corpus(
        LEGACY, ROOT, strict_layout=False, check_manifest=False
    )
    duplicates = {f.item_id for f in findings if f.code == "DUPLICATE_ID"}
    assert duplicates == LEGACY_DUPLICATE_IDS


@pytest.mark.skipif(not LEGACY.is_dir(), reason="legacy corpus removed")
def test_legacy_corpus_broken_cross_link_is_detected():
    """breeding.pregnancy points at breeding.abortion, which does not exist.

    The real item is breeding.abortion-or-loss. The old validator never resolved
    this link because the item declaring it was one of the nested nine.
    """
    findings = validate_corpus(
        LEGACY, ROOT, strict_layout=False, check_manifest=False
    )
    broken = [f for f in findings if f.code == "BROKEN_RELATED"]
    assert len(broken) == 1
    assert broken[0].item_id == "breeding.pregnancy"
    assert "breeding.abortion" in broken[0].message


@pytest.mark.skipif(not LEGACY.is_dir(), reason="legacy corpus removed")
def test_legacy_corpus_simulator_reference_is_detected():
    """The Training Simulator was retired; the corpus must not teach one."""
    findings = validate_corpus(
        LEGACY, ROOT, strict_layout=False, check_manifest=False
    )
    assert any(f.code == "SIMULATOR_REFERENCE" for f in findings)


# ---------------------------------------------------------------------------
# The validator's own behaviour
# ---------------------------------------------------------------------------


def test_broken_anchor_is_detected(tmp_path: Path):
    """Regression for a real authoring bug.

    An ad hoc check resolved anchors with ``Path(".").parent``, which is ``.``,
    and reported forty phantom missing anchors. This test fixes the contract:
    a real anchor passes, a fabricated one fails, and both are judged against an
    explicit repository root.
    """
    corpus = _write_corpus(
        tmp_path / "corpus",
        [
            _item(
                id="demo.real-anchor",
                status="IMPLEMENTATION_REVIEW",
                explanation="x",
                alternatives=["a", "b"],
                verified_against_source="deadbeef",
                implementation_reviewed_by=None,
                implementation_reviewed_at=None,
                anchors={"components": [], "services": ["pyproject.toml"], "models": [], "tests": []},
            ),
            _item(
                id="demo.fake-anchor",
                status="IMPLEMENTATION_REVIEW",
                explanation="x",
                alternatives=["a", "b"],
                verified_against_source="deadbeef",
                implementation_reviewed_by=None,
                implementation_reviewed_at=None,
                anchors={"components": [], "services": ["src/does/not/exist.py"], "models": [], "tests": []},
            ),
        ],
    )
    findings = validate_corpus(corpus, ROOT, check_manifest=False)
    missing = [f for f in findings if f.code == "MISSING_ANCHOR"]
    assert [f.item_id for f in missing] == ["demo.fake-anchor"]


def test_nested_item_is_detected(tmp_path: Path):
    """The exact shape that hid nine items from the previous validator."""
    root = tmp_path / "corpus"
    root.mkdir(parents=True)
    (root / "nested.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "domains": [{"id": "demo-domain", "items": [_item(id="demo.nested")]}],
            }
        ),
        encoding="utf-8",
    )
    findings = validate_corpus(root, ROOT, check_manifest=False)
    assert "NESTED_ITEM" in codes(findings)
    # and crucially the item is still found, so its other defects surface too
    assert any(f.item_id == "demo.nested" for f in findings)


def test_capability_coverage_is_scoped_to_its_domain(tmp_path: Path):
    """An item in one domain must not satisfy another domain's capability.

    In the legacy corpus ``dashboard.resolution`` satisfied the Health domain's
    ``resolution`` and ``assistant.answer-contract`` satisfied Breeding's ``ai``,
    so two undocumented capabilities were reported as full coverage.
    """
    catalogue = {
        "domains": [
            {"id": "alpha", "capabilities": ["shared-name", "alpha-only"]},
            {"id": "beta", "capabilities": ["shared-name"]},
        ]
    }
    corpus = _write_corpus(
        tmp_path / "corpus",
        [
            _item(id="alpha.one", domain="alpha", capability="shared-name"),
            _item(id="beta.one", domain="beta", capability="shared-name"),
        ],
        catalogue=catalogue,
    )
    findings = validate_corpus(corpus, ROOT, check_manifest=False)
    undocumented = [f for f in findings if f.code == "UNDOCUMENTED_CAPABILITY"]
    assert len(undocumented) == 1
    assert "alpha-only" in undocumented[0].message


def test_example_identifiers_must_use_the_reserved_namespace(tmp_path: Path):
    """Worked examples must be obviously fictional, never a real farm id."""
    corpus = _write_corpus(
        tmp_path / "corpus",
        [
            _item(id="demo.good", answer="Consider cow EX-COW-001."),
            _item(id="demo.bad", answer="Consider cow TD-001."),
        ],
    )
    findings = validate_corpus(corpus, ROOT, check_manifest=False)
    offenders = {f.item_id for f in findings if f.code == "NON_RESERVED_EXAMPLE_ID"}
    assert offenders == {"demo.bad"}


def test_approved_status_requires_a_recorded_domain_review(tmp_path: Path):
    """Only APPROVED items are servable, so approval must carry its evidence."""
    corpus = _write_corpus(
        tmp_path / "corpus",
        [
            _item(
                id="demo.approved",
                status="APPROVED",
                explanation="x",
                alternatives=["a", "b"],
                anchors={},
                verified_against_source="deadbeef",
                implementation_reviewed_by="someone",
                implementation_reviewed_at="2026-09-18",
                perspectives={
                    k: "NOT_APPLICABLE"
                    for k in (
                        "operator",
                        "supervisor",
                        "finance",
                        "veterinary_health",
                        "technical",
                        "training",
                        "troubleshooting",
                    )
                },
                exceptions=[],
                correction_path="x",
                domain_reviewed_by="",
                domain_reviewed_at=None,
            )
        ],
    )
    findings = validate_corpus(corpus, ROOT, check_manifest=False)
    assert "UNREVIEWED_APPROVAL" in codes(findings)


# ---------------------------------------------------------------------------
# The boundary, asserted statically
# ---------------------------------------------------------------------------


def test_assistant_package_never_imports_the_operational_package():
    """The Assistant's whole purpose depends on having no route to farm data."""
    offenders: list[str] = []
    for path in ASSISTANT_PACKAGE.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import dairyos.", "from dairyos.")) or stripped in {
                "import dairyos",
                "from dairyos import",
            }:
                offenders.append(f"{path.relative_to(ROOT)}: {stripped}")
    assert offenders == [], f"dairyos_assistant must not import dairyos: {offenders}"


def test_assistant_package_imports_no_database_or_search_client():
    forbidden = ("sqlalchemy", "psycopg", "alembic", "elasticsearch", "dotenv")
    offenders: list[str] = []
    for path in ASSISTANT_PACKAGE.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            for name in forbidden:
                if f" {name}" in stripped or stripped.startswith(f"from {name}"):
                    offenders.append(f"{path.relative_to(ROOT)}: {stripped}")
    assert offenders == [], f"forbidden client imported: {offenders}"

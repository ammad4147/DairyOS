"""Knowledge governance: deterministic manifest, provenance, review semantics and freshness."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from dairyos_assistant.corpus.validation import errors, validate_corpus
from dairyos_assistant_tools import kb_build

ROOT = Path(__file__).resolve().parents[2]
KB = ROOT / "docs" / "assistant-knowledge"


def test_shipped_corpus_validates_and_reconciles_with_its_manifest():
    findings = validate_corpus(KB)
    assert errors(findings) == [], [str(f) for f in findings]


def test_build_is_deterministic_and_matches_the_committed_corpus():
    result = kb_build.build(ROOT)
    assert result.errors == [], [str(f) for f in result.errors]
    committed = json.loads((KB / "corpus.json").read_text(encoding="utf-8"))
    assert result.corpus == committed, "corpus.json is out of date; run tools/assistant_kb.py build"


def test_manifest_counts_are_computed_not_typed():
    manifest = json.loads((KB / "manifest.json").read_text(encoding="utf-8"))
    counts = manifest["counts"]
    for name in ("by_collection", "by_kind", "by_review_status", "by_freshness", "by_safety_class"):
        assert sum(counts[name].values()) == counts["total"], name
    assert sum(f["record_count"] for f in manifest["files"]) == counts["total"]


def test_no_record_is_stale_against_current_source():
    assert kb_build.build(ROOT).stale == []


def test_review_status_means_what_it_says():
    corpus = json.loads((KB / "corpus.json").read_text(encoding="utf-8"))
    for record in corpus["records"]:
        review = record["review"]
        if review["status"] == "VET_REVIEWED":
            assert review.get("reviewer"), record["id"]
        if record["collection"] == "dairy":
            assert review["status"] != "ENGINEERING_VERIFIED", record["id"]
            assert record["provenance"], record["id"]
            assert all(p.get("url") and p.get("publisher") for p in record["provenance"]), record["id"]


@pytest.fixture
def repo_copy(tmp_path):
    """A minimal copy of the repository: knowledge sources plus every anchored source file."""
    target = tmp_path / "repo"
    shutil.copytree(KB, target / "docs" / "assistant-knowledge")
    corpus = json.loads((KB / "corpus.json").read_text(encoding="utf-8"))
    for record in corpus["records"]:
        for key in record.get("anchor_hashes", {}):
            path = key.split("::")[0]
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, destination)
    return target


def test_a_source_change_marks_only_the_affected_records_stale_until_revalidated(repo_copy):
    """Controlled source change: the policy constant behind breeding knowledge is edited."""
    path = repo_copy / "src/dairyos/farm/reproduction/services/reproductive_state_service.py"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("voluntary_waiting_period_days=45", "voluntary_waiting_period_days=50"), encoding="utf-8")

    result = kb_build.build(repo_copy)
    stale = set(result.stale)
    assert "breeding.pd" in stale  # anchored on DEFAULT_REPRODUCTIVE_POLICY
    assert "milk.record.session" not in stale  # unaffected knowledge stays current
    assert any(f.code == "STALE" for f in result.findings)

    kb_build.verify(repo_copy, ["breeding.pd", "breeding.vwp"], reviewer="test reviewer", when="2026-09-22")
    after = set(kb_build.build(repo_copy).stale)
    assert "breeding.pd" not in after


def test_a_removed_ui_label_breaks_its_anchor(repo_copy):
    path = repo_copy / "src/DairyOS.Web/src/components/MilkTab.tsx"
    path.write_text(path.read_text(encoding="utf-8").replace("Enter Missing Milk", "Enter Late Milk"), encoding="utf-8")
    result = kb_build.build(repo_copy)
    assert any(f.code == "BROKEN_ANCHOR" and f.record == "milk.missed-session" for f in result.findings)


def test_a_dairy_record_without_provenance_fails(repo_copy):
    path = repo_copy / "docs/assistant-knowledge/source/dairy-calves.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("  provenance:\n  - {source: UW-NAVEL}\n", "  provenance: []\n", 1), encoding="utf-8")
    result = kb_build.build(repo_copy)
    assert any(f.record == "dairy.calf.navel-care" for f in result.errors)

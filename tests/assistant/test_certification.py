"""The AA-16 certification gate.

These tests are skipped during development and are the checks that must pass
before the Assistant is certified for release. They are written now, while the
reasons for them are fresh, rather than at the end when the temptation to write
a lenient version of them will be strongest.

Run them with::

    DAIRYOS_ASSISTANT_CERTIFY=1 pytest tests/assistant/test_certification.py

A skipped test is not a passing test, and this module is reported as skipped in
every gate report until AA-16 so that its absence from the pass count cannot be
mistaken for coverage.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from dairyos_assistant import release
from dairyos_assistant.corpus.validation import SERVABLE_STATUSES, load_corpus
from dairyos_assistant.retrieval import KnowledgeIndex


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs" / "assistant-knowledge"

pytestmark = pytest.mark.skipif(
    not os.environ.get("DAIRYOS_ASSISTANT_CERTIFY"),
    reason="AA-16 certification gate; set DAIRYOS_ASSISTANT_CERTIFY=1 to run",
)


def test_the_build_is_not_a_pre_release_build():
    """The single switch that lets unreviewed knowledge be served."""
    assert release.PRE_RELEASE is False, (
        "PRE_RELEASE is still true, so this build serves implementation-reviewed "
        "content that no domain reviewer has approved. It must be set false in "
        "src/dairyos_assistant/release.py before certification."
    )


def test_the_index_serves_only_approved_content():
    index = KnowledgeIndex.load(CORPUS)
    assert index.servable_statuses == frozenset(SERVABLE_STATUSES)
    report = index.status_report()
    assert report["serving_unreviewed"] is False
    assert report["pre_release_build"] is False


def test_the_corpus_actually_has_approved_content():
    """A certified build that serves nothing is not a certified build."""
    index = KnowledgeIndex.load(CORPUS)
    assert index.servable_count > 0, (
        "no item in the corpus has reached APPROVED, so a correctly certified "
        "Assistant would answer nothing"
    )


def test_every_approved_item_names_its_domain_reviewer():
    """Operator decision of 2026-09-18: clinical content is signed by a named
    veterinarian, not by the implementer and not by this agent."""
    unsigned: list[str] = []
    for entry in load_corpus(CORPUS).items:
        item = entry.item
        if item.get("status") != "APPROVED":
            continue
        reviewer = str(item.get("domain_reviewed_by", "")).strip()
        if not reviewer or reviewer.lower() in {"claude", "assistant", "ai", "unknown"}:
            unsigned.append(f"{item.get('id')}: domain_reviewed_by={reviewer!r}")
    assert unsigned == [], f"approved items without a named domain reviewer: {unsigned}"


def test_the_manifest_records_the_source_it_was_verified_against():
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    assert manifest.get("dairyos_source_authority"), (
        "the corpus must record which DairyOS commit its claims were traced to"
    )
    assert manifest.get("servable_statuses") == ["APPROVED"]

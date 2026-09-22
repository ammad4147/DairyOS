"""Build the veterinary review pack from the compiled Assistant knowledge.

Domain review is the gate between curated knowledge and approved knowledge, and
it cannot be satisfied by a name typed into a field. This produces the document
a veterinarian can actually read: every dairy record the Assistant serves, in
full, with its sources, its escalation wording and a place to record a verdict.

Records are grouped by safety class so the reviewer can start with the items
that carry the most risk (VET_ONLY, then TRIAGE, then EDUCATIONAL).

The verdicts are applied back to the YAML sources by an engineer (review status
VET_REVIEWED with the reviewer's name and date); ``tools/assistant_kb.py build``
then recomputes the manifest. Nothing in this pack changes the corpus by itself.

Output is a single self-contained HTML file that prints cleanly, so it can be
emailed, printed or saved as PDF without anything being installed.

    python tools/build_review_pack.py [--out PATH]
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "docs" / "assistant-knowledge"
OUT = KB / "veterinary-review-pack.html"
ORDER = ("VET_ONLY", "TRIAGE", "EDUCATIONAL")

CSS = """
body{font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#1b1b1b;line-height:1.45}
h1{font-size:22px;margin-bottom:4px} h2{font-size:18px;border-bottom:2px solid #2f5d50;padding-bottom:4px;margin-top:32px}
.rec{border:1px solid #c8c8c8;border-radius:6px;padding:12px 16px;margin:14px 0;page-break-inside:avoid}
.rec h3{font-size:15px;margin:0 0 4px} .meta{color:#555;font-size:12px} .esc{background:#fff4e5;border-left:4px solid #d9822b;padding:6px 10px;margin:8px 0}
.verdict{border-top:1px dashed #999;margin-top:10px;padding-top:8px;font-size:13px}
.box{display:inline-block;width:12px;height:12px;border:1px solid #333;margin:0 4px 0 12px;vertical-align:middle}
.line{border-bottom:1px solid #999;height:22px;margin-top:6px} small a{color:#2f5d50}
"""


def _e(value) -> str:
    return html.escape(str(value or ""))


def _record(r: dict) -> str:
    safety = r.get("safety") or {}
    parts = [f'<div class="rec"><h3>{_e(r["title"])}</h3>',
             f'<div class="meta">{_e(r["id"])} &middot; {_e(r["kind"])} &middot; safety {_e(safety.get("class"))}'
             f' &middot; current status {_e(r["review"]["status"])}</div>']
    if r.get("questions"):
        parts.append("<p><b>Operators ask:</b> " + "; ".join(_e(q) for q in r["questions"][:4]) + "</p>")
    parts.append(f"<p><b>Summary served:</b> {_e(r['summary'])}</p>")
    if r.get("facts"):
        parts.append("<ol>" + "".join(f"<li>{_e(f)}</li>" for f in r["facts"]) + "</ol>")
    if safety.get("escalate"):
        parts.append(f'<div class="esc"><b>Veterinary escalation wording:</b> {_e(safety["escalate"])}</div>')
    sources = [f'<a href="{_e(p.get("url"))}">{_e(p.get("publisher"))}: {_e(p.get("title"))}</a>'
               + (f" ({_e(p['revised'])})" if p.get("revised") else "") for p in r.get("provenance") or []]
    if sources:
        parts.append("<small><b>Sources:</b> " + "; ".join(sources) + "</small>")
    parts.append('<div class="verdict">Verdict:<span class="box"></span>Approve'
                 '<span class="box"></span>Approve with changes<span class="box"></span>Reject'
                 '<div class="line">Changes / comments:</div><div class="line"></div></div></div>')
    return "".join(parts)


def build(out: Path = OUT) -> Path:
    corpus = json.loads((KB / "corpus.json").read_text(encoding="utf-8"))
    records = [r for r in corpus["records"] if r["collection"] == "dairy" and r.get("servable", True)]
    body = [f"<h1>DairyOS Assistant: veterinary review pack</h1>",
            f"<p class='meta'>Generated {date.today().isoformat()} from corpus schema "
            f"{_e(corpus.get('schema_version'))}. {len(records)} dairy records.</p>",
            "<p>Each record below is what the Assistant may tell an operator. It is general education and "
            "triage; the Assistant never diagnoses, names a medicine or gives a dose. Please mark each record, "
            "correct any wording, and confirm that the escalation text sends the operator to a veterinarian "
            "at the right point. Reviewer name, registration and date:</p><div class='line'></div>"]
    for cls in ORDER:
        group = sorted((r for r in records if (r.get("safety") or {}).get("class") == cls), key=lambda r: r["id"])
        if group:
            body.append(f"<h2>{cls.replace('_', ' ').title()} ({len(group)})</h2>")
            body.extend(_record(r) for r in group)
    out.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>Veterinary review pack</title>"
                   f"<style>{CSS}</style></head><body>{''.join(body)}</body></html>", encoding="utf-8")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT)
    print(build(parser.parse_args().out))

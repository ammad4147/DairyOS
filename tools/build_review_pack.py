"""Build the veterinary review pack.

Domain review is the gate between an authored corpus and an approved one, and
it cannot be satisfied by a name typed into a field. This produces the document
a veterinarian can actually read: every clinical item, in full, with a place to
record a verdict against each one.

Deprecated items are excluded. They exist to redirect, never to answer, so they
are not served and reviewing them would waste the reviewer's time.

Output is a single self-contained HTML file that prints cleanly, so it can be
emailed, printed, or saved as PDF without anything being installed.
"""

from __future__ import annotations

import glob
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "docs" / "assistant-knowledge"
OUT = ROOT / "docs" / "assistant-knowledge" / "veterinary-review-pack.html"

CLINICAL_DOMAINS = ("health", "vaccination", "breeding")

SECTIONS = (
    ("question", "Question as an operator would ask it"),
    ("answer", "Answer the Assistant gives"),
    ("explanation", "Explanation"),
    ("exceptions", "Exceptions"),
    ("correction_path", "How a mistake is corrected"),
)


def load_items() -> dict[str, dict]:
    items: dict[str, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            if "id" in node and "status" in node:
                items[node["id"]] = node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for path in glob.glob(str(CORPUS / "**" / "*.json"), recursive=True):
        if path.endswith("manifest.json"):
            continue
        walk(json.loads(Path(path).read_text(encoding="utf-8")))
    return items


def render_value(value) -> str:
    if isinstance(value, list):
        parts = []
        for entry in value:
            if isinstance(entry, dict):
                condition = entry.get("condition", "")
                behaviour = entry.get("behaviour", "")
                parts.append(f"<li><b>{html.escape(str(condition))}</b> {html.escape(str(behaviour))}</li>")
            else:
                parts.append(f"<li>{html.escape(str(entry))}</li>")
        return "<ul>" + "".join(parts) + "</ul>"
    return f"<p>{html.escape(str(value))}</p>"


def main() -> int:
    items = load_items()
    clinical = [
        item
        for key, item in sorted(items.items())
        if key.split(".")[0] in CLINICAL_DOMAINS
        and item.get("status") != "DEPRECATED"
        and "redirect_to" not in item
    ]

    blocks = []
    for index, item in enumerate(clinical, start=1):
        rows = []
        for field, label in SECTIONS:
            value = item.get(field)
            if not value:
                continue
            rows.append(f"<h4>{html.escape(label)}</h4>{render_value(value)}")
        blocks.append(
            f"""
<section>
  <h3>{index}. {html.escape(str(item.get('title', item['id'])))}
      <span class="id">{html.escape(item['id'])}</span></h3>
  {''.join(rows)}
  <table class="verdict">
    <tr><th>Verdict</th><td>Correct as written &nbsp;&nbsp; / &nbsp;&nbsp; Correct with the change below
        &nbsp;&nbsp; / &nbsp;&nbsp; Not correct</td></tr>
    <tr><th>Correction or comment</th><td class="write"></td></tr>
  </table>
</section>"""
        )

    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>DairyOS Assistant: veterinary review pack</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; max-width: 46em; margin: 2em auto;
         padding: 0 1.5em; line-height: 1.55; color: #111; }}
  h1 {{ font-size: 1.6em; margin-bottom: 0.2em; }}
  h3 {{ margin-top: 2em; border-bottom: 1px solid #ccc; padding-bottom: 0.3em; font-size: 1.1em; }}
  h4 {{ margin: 1.1em 0 0.3em; font-size: 0.85em; text-transform: uppercase;
        letter-spacing: 0.06em; color: #555; font-weight: normal; }}
  .id {{ float: right; font-family: monospace; font-size: 0.7em; color: #888; font-weight: normal; }}
  .intro {{ background: #f6f6f4; border-left: 3px solid #999; padding: 1em 1.2em; margin: 1.5em 0; }}
  table.verdict {{ width: 100%; border-collapse: collapse; margin-top: 1.2em; }}
  table.verdict th {{ text-align: left; width: 11em; vertical-align: top; padding: 0.5em 0.6em;
                      font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.05em;
                      color: #555; font-weight: normal; border: 1px solid #bbb; background: #fafafa; }}
  table.verdict td {{ padding: 0.5em 0.6em; border: 1px solid #bbb; font-size: 0.9em; }}
  td.write {{ height: 4.5em; }}
  ul {{ margin: 0.3em 0 0.3em 1.2em; padding: 0; }}
  section {{ page-break-inside: avoid; }}
  @media print {{ body {{ margin: 0; max-width: none; }} }}
</style></head><body>

<h1>DairyOS Assistant: veterinary review</h1>
<p><b>Reviewer:</b> Dr Umair Shaffi &nbsp;&nbsp;|&nbsp;&nbsp;
   <b>Corpus version:</b> 0.4.0 &nbsp;&nbsp;|&nbsp;&nbsp;
   <b>Prepared:</b> {date.today().isoformat()} &nbsp;&nbsp;|&nbsp;&nbsp;
   <b>Items:</b> {len(clinical)}</p>

<div class="intro">
<p>This is the clinical content of a knowledge assistant built into DairyOS. The
assistant teaches farm staff how the software works and what the terms mean. It
has no access to any farm's records and cannot see a single animal, so nothing
here is advice about a patient; it is general guidance that will be repeated to
operators verbatim.</p>

<p>What matters in this review is whether each statement is correct as a general
statement of dairy practice, and whether anything here could lead an operator to
act unsafely. Software behaviour, screen names and record-keeping rules have
already been checked against the source code and are not the subject of this
review.</p>

<p>Mark each item and return the document. An item is only made available to
operators once it carries a reviewer's name, so anything left unmarked stays
withheld rather than being published unreviewed.</p>
</div>

{''.join(blocks)}

<section>
  <h3>Reviewer declaration</h3>
  <table class="verdict">
    <tr><th>Name and qualification</th><td class="write"></td></tr>
    <tr><th>Signature</th><td class="write"></td></tr>
    <tr><th>Date</th><td class="write"></td></tr>
  </table>
</section>

</body></html>"""

    OUT.write_text(document, encoding="utf-8", newline="\n")
    print(f"{len(clinical)} clinical items written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

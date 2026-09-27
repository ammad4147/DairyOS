import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_every_test_path_named_in_a_workflow_exists():
    missing = []
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8-sig")
        for path in sorted(set(re.findall(r"\btests/[\w/.-]+\.py\b", text))):
            if not (ROOT / path).is_file():
                missing.append(f"{workflow.name}: {path}")
    assert missing == []

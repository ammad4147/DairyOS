import re
import subprocess
from pathlib import PurePosixPath


DEBRIS_PATTERNS = (
    re.compile(r"\.g\d+-backup$", re.IGNORECASE),
    re.compile(r"\.corrupted-\d{8}-\d{6}\.bak$", re.IGNORECASE),
    re.compile(r"\.bak[_-]\d{8}", re.IGNORECASE),
)

EXACT_DEBRIS = {
    ".dairyos-final-surface-remediation-trigger",
    ".github/workflows/final-surface-fix.yml",
}


def test_tracked_repository_contains_no_remediation_debris():
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    paths = [
        item.decode("utf-8").replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    ]

    offenders = []
    for path in paths:
        name = PurePosixPath(path).name
        if path in EXACT_DEBRIS or any(pattern.search(name) for pattern in DEBRIS_PATTERNS):
            offenders.append(path)

    assert offenders == [], f"Tracked remediation debris: {offenders}"

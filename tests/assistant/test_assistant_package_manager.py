import json
import zipfile
from pathlib import Path

import pytest

from dairyos import assistant_package


def _package(tmp_path: Path) -> Path:
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "DairyOSAssistant.exe").write_bytes(b"assistant")
    (payload / "assistant-manifest.json").write_text(
        json.dumps({
            "package_id": "dairyos-assistant",
            "assistant_version": "0.1.0",
            "compatible_core": ">=0.1.0 <0.2.0",
        }),
        encoding="utf-8",
    )
    package = tmp_path / "DairyOS-Assistant-Pack.zip"
    with zipfile.ZipFile(package, "w") as archive:
        for path in payload.iterdir():
            archive.write(path, path.name)
    return package


def test_missing_package_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(assistant_package, "ASSISTANT_ROOT", tmp_path / "assistant")
    with pytest.raises(FileNotFoundError):
        assistant_package.install(tmp_path / "missing.zip")


def test_package_install_is_staged_and_manifest_driven(tmp_path, monkeypatch):
    package = _package(tmp_path)
    root = tmp_path / "assistant"
    monkeypatch.setattr(assistant_package, "ASSISTANT_ROOT", root)

    result = assistant_package.install(package)

    assert result["installed"] is True
    assert json.loads((root / "assistant-manifest.json").read_text())[
        "assistant_version"
    ] == "0.1.0"
    assert (root / "DairyOSAssistant.exe").is_file()

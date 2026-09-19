from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_standalone_assistant_spec_exists_and_core_collection_excludes_assistant():
    assistant_spec = (ROOT / "DairyOS-Assistant.spec").read_text(encoding="utf-8")
    core_spec = (ROOT / "DairyOS.spec").read_text(encoding="utf-8")
    assert "DairyOSAssistant" in assistant_spec
    assert "assistant-knowledge" in assistant_spec
    assert "DairyOSAssistant" not in core_spec.split("coll = COLLECT(", 1)[1]


def test_assistant_builder_records_governed_manifest_and_integrity():
    source = (ROOT / "scripts" / "Build-DairyOS-Assistant.ps1").read_text(
        encoding="utf-8"
    )
    for token in (
        "package_id",
        "assistant_version",
        "compatible_core",
        "model_identity",
        "runtime_identity",
        "source_commit",
        "sha256",
        "package_size_bytes",
        "Get-FileHash",
    ):
        assert token in source


def test_core_keeps_private_postgresql_packaging():
    source = (ROOT / "scripts" / "Build-DairyOS-Desktop.ps1").read_text(
        encoding="utf-8"
    )
    assert "COPY PRIVATE POSTGRESQL RUNTIME" in source
    assert "PostgreSQL" in source

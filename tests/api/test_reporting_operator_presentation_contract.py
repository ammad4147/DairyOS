from pathlib import Path

from dairyos.api.reporting_export import csv_bytes, pdf_bytes, xlsx_bytes


ROOT = Path(__file__).resolve().parents[2]
REPORTING_TAB = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "ReportingTab.tsx"


def test_operator_reporting_hides_developer_authority_matrix_and_raw_print_window():
    source = REPORTING_TAB.read_text(encoding="utf-8")
    assert "Report Catalog and Authority Matrix" not in source
    assert "window.print(" not in source
    assert "printWindow.print(" not in source
    assert "document.createElement('iframe')" not in source
    assert "print-ready PDF" in source


def test_operator_reporting_has_readable_table_contract():
    source = REPORTING_TAB.read_text(encoding="utf-8")
    assert "humanize(column)" in source
    assert "displayValue(row[column])" in source
    assert "overflow-x-auto" in source
    assert "whitespace-normal break-words" in source


def test_csv_uses_operator_facing_headings():
    payload = csv_bytes(["animal_id", "event_type"], [{"animal_id": "A-001", "event_type": "CONFIRMED_PREGNANT"}]).decode("utf-8-sig")
    assert payload.splitlines()[0] == "Animal ID,Event Type"
    assert "animal_id" not in payload.splitlines()[0]


def test_pdf_and_xlsx_are_genuine_after_readability_remediation():
    columns = ["animal_id", "event_type"]
    rows = [{"animal_id": "A-001", "event_type": "AI"}]
    assert pdf_bytes("Breeding", columns, rows, {"record_count": 1}).startswith(b"%PDF")
    assert xlsx_bytes("Breeding", columns, rows, {"record_count": 1}).startswith(b"PK")

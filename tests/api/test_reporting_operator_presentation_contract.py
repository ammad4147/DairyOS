from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm

from dairyos.api.reporting_export import (
    PDF_LANDSCAPE_COLUMN_THRESHOLD,
    PDF_MARGIN,
    _pdf_page_size,
    csv_bytes,
    pdf_bytes,
    xlsx_bytes,
)


ROOT = Path(__file__).resolve().parents[2]
REPORTING_TAB = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "ReportingTab.tsx"


def test_operator_reporting_hides_developer_authority_matrix_and_raw_print_window():
    source = REPORTING_TAB.read_text(encoding="utf-8")
    assert "Report Catalog and Authority Matrix" not in source
    assert "window.print(" not in source
    assert "printWindow.print(" not in source
    assert "document.createElement('iframe')" not in source
    assert "await downloadExport('PDF', '-Print')" in source
    assert "Print-ready PDF saved." in source


def test_operator_reporting_has_readable_table_contract():
    source = REPORTING_TAB.read_text(encoding="utf-8")
    assert "const labelFor =" in source
    assert "columnLabels[value] || humanize(value)" in source
    assert "{labelFor(column)}" in source
    assert "displayValue(row[column])" in source
    assert "overflow-x-auto" in source
    assert "whitespace-normal break-words" in source


def test_csv_uses_operator_facing_headings():
    payload = csv_bytes(["animal_id", "event_type"], [{"animal_id": "A-001", "event_type": "CONFIRMED_PREGNANT"}]).decode("utf-8-sig")
    assert payload.splitlines()[0] == "Animal ID,Event Type"
    assert "animal_id" not in payload.splitlines()[0]


def test_operator_units_and_currency_headings_match_across_csv_and_xlsx():
    columns = ["total_yield", "quantity_liters", "amount", "feed_cost_per_litre_today"]
    row = {"total_yield": 90.0, "quantity_liters": 75.0, "amount": 15000.0, "feed_cost_per_litre_today": 32.5}
    expected = ["Total Milk (L)", "Quantity (L)", "Amount (PKR)", "Feed Cost / Litre (PKR)"]

    csv_payload = csv_bytes(columns, [row]).decode("utf-8-sig")
    assert csv_payload.splitlines()[0].split(",") == expected

    workbook = load_workbook(BytesIO(xlsx_bytes("Farm Report", columns, [row], {})), data_only=True)
    assert list(next(workbook["Report"].values)) == expected


def test_reporting_pdf_page_settings_are_explicit_a4_with_10mm_margins():
    assert PDF_MARGIN == 10 * mm
    assert PDF_LANDSCAPE_COLUMN_THRESHOLD == 6
    assert _pdf_page_size([f"column_{index}" for index in range(6)]) == portrait(A4)
    assert _pdf_page_size([f"column_{index}" for index in range(7)]) == landscape(A4)


def test_reporting_pdf_table_contract_repeats_header_and_fits_printable_width():
    source = (ROOT / "src" / "dairyos" / "api" / "reporting_export.py").read_text(encoding="utf-8")
    assert "repeatRows=1" in source
    assert "available_width = page_size[0] - (2 * PDF_MARGIN)" in source
    assert "colWidths=widths" in source
    assert 'Paragraph(_heading(column), header_style)' in source
    assert 'Paragraph(_cell(row.get(column)), body_style)' in source


def test_pdf_and_xlsx_are_genuine_after_readability_remediation():
    columns = ["animal_id", "event_type"]
    rows = [{"animal_id": "A-001", "event_type": "AI"}]
    assert pdf_bytes("Breeding", columns, rows, {"record_count": 1}).startswith(b"%PDF")
    assert xlsx_bytes("Breeding", columns, rows, {"record_count": 1}).startswith(b"PK")

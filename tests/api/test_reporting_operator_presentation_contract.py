from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm

from dairyos.api.reporting import ReportingRequest, _project_dataset
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
REPORTING_EXPORT = ROOT / "src" / "dairyos" / "api" / "reporting_export.py"


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


def test_operator_can_choose_governed_columns_without_redesigning_reporting():
    source = REPORTING_TAB.read_text(encoding="utf-8")
    assert "Fields / Columns" in source
    assert "Select All" in source
    assert ">Clear<" in source
    assert "selected_columns: selectedColumns" in source
    assert "X-DairyOS-Column-Count" in source
    assert "Select at least one field or column." in source


def test_reporting_request_accepts_unique_selected_columns():
    request = ReportingRequest(report_id="animal-register", domain="ANIMALS", period_mode="CURRENT_HERD", selected_columns=["animal_id", "category"])
    assert request.selected_columns == ["animal_id", "category"]


def test_projection_preserves_requested_order_and_does_not_change_summary():
    dataset = {"dataset_status":"AUTHORITATIVE_DATASET","authority_status":"AUTHORITY_AVAILABLE","columns":["animal_id","category","status"],"rows":[{"animal_id":"A-001","category":"Milking","status":"ACTIVE"}],"summary":{"records":1},"warnings":[]}
    projected = _project_dataset(dataset, ["category", "animal_id"])
    assert projected["columns"] == ["category", "animal_id"]
    assert projected["rows"] == [{"category":"Milking","animal_id":"A-001"}]
    assert projected["summary"] == {"records":1}


def test_csv_uses_operator_facing_headings():
    payload = csv_bytes(["animal_id", "event_type"], [{"animal_id":"A-001","event_type":"CONFIRMED_PREGNANT"}]).decode("utf-8-sig")
    assert payload.splitlines()[0] == "Animal ID,Event Type"
    assert "animal_id" not in payload.splitlines()[0]


def test_operator_units_and_currency_headings_match_across_csv_and_xlsx():
    columns = ["total_yield", "quantity_liters", "amount", "feed_cost_per_litre_today"]
    row = {"total_yield":90.0,"quantity_liters":75.0,"amount":15000.0,"feed_cost_per_litre_today":32.5}
    expected = ["Total Milk (L)", "Quantity (L)", "Amount (PKR)", "Feed Cost / Litre (PKR)"]
    assert csv_bytes(columns, [row]).decode("utf-8-sig").splitlines()[0].split(",") == expected
    workbook = load_workbook(BytesIO(xlsx_bytes("Farm Report", columns, [row], {})), data_only=True)
    assert list(next(workbook["Report"].values)) == expected


def test_pdf_page_settings_are_governed_for_print_readability():
    source = REPORTING_EXPORT.read_text(encoding="utf-8")
    assert PDF_MARGIN == 10 * mm
    assert PDF_LANDSCAPE_COLUMN_THRESHOLD == 6
    assert "return landscape(A4) if len(columns) > PDF_LANDSCAPE_COLUMN_THRESHOLD else portrait(A4)" in source
    assert "leftMargin=PDF_MARGIN" in source
    assert "rightMargin=PDF_MARGIN" in source
    assert "topMargin=PDF_MARGIN" in source
    assert "bottomMargin=PDF_MARGIN" in source
    assert "available_width = page_size[0] - (2 * PDF_MARGIN)" in source
    assert "repeatRows=1" in source
    assert "colWidths=widths" in source
    assert "Paragraph(_heading(column), header_style)" in source
    assert "Paragraph(_cell(row.get(column)), body_style)" in source


def test_pdf_orientation_threshold_keeps_six_columns_portrait_and_seven_landscape():
    assert _pdf_page_size([f"field_{index}" for index in range(6)]) == portrait(A4)
    assert _pdf_page_size([f"field_{index}" for index in range(7)]) == landscape(A4)


def test_pdf_and_xlsx_are_genuine_after_readability_remediation():
    columns = ["animal_id", "event_type"]
    rows = [{"animal_id":"A-001","event_type":"AI"}]
    assert pdf_bytes("Breeding", columns, rows, {"record_count":1}).startswith(b"%PDF")
    assert xlsx_bytes("Breeding", columns, rows, {"record_count":1}).startswith(b"PK")

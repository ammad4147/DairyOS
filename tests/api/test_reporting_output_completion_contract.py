from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from dairyos.api.reporting_export import csv_bytes, pdf_bytes, xlsx_bytes


ROOT = Path(__file__).resolve().parents[2]
REPORTING_API = ROOT / "src" / "dairyos" / "api" / "reporting.py"
REPORTING_EXPORT = ROOT / "src" / "dairyos" / "api" / "reporting_export.py"
REPORTING_UI = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "ReportingTab.tsx"
PYPROJECT = ROOT / "pyproject.toml"


def test_reporting_api_exposes_canonical_export_endpoint():
    source = REPORTING_API.read_text(encoding="utf-8")
    assert '@router.post("/export")' in source
    assert "reporting_export" in source
    assert "_reporting_payload(payload,container)" in source


def test_reporting_dependencies_include_real_pdf_and_xlsx_writers():
    source = PYPROJECT.read_text(encoding="utf-8").lower()
    assert "openpyxl" in source
    assert "reportlab" in source


def test_reporting_api_generates_real_csv_xlsx_and_pdf_payloads():
    api_source = REPORTING_API.read_text(encoding="utf-8")
    exporter_source = REPORTING_EXPORT.read_text(encoding="utf-8").lower()
    assert "text/csv" in api_source
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in api_source
    assert "application/pdf" in api_source
    assert "openpyxl" in exporter_source
    assert "reportlab" in exporter_source


def test_exporter_bytes_are_real_formats_and_reconcile_rows():
    columns = ["animal_id", "liters"]
    rows = [{"animal_id": "T-001", "liters": 12.5}, {"animal_id": "T-002", "liters": 0}]
    summary = {"active_milk_liters": 12.5, "records": 2}

    csv_payload = csv_bytes(columns, rows)
    assert csv_payload.startswith(b"\xef\xbb\xbf")
    csv_text = csv_payload.decode("utf-8-sig")
    assert "T-001" in csv_text and "12.5" in csv_text and "T-002" in csv_text

    xlsx_payload = xlsx_bytes("Daily Milk Production", columns, rows, summary)
    assert xlsx_payload.startswith(b"PK")
    workbook = load_workbook(BytesIO(xlsx_payload), data_only=True)
    sheet = workbook["Report"]
    assert list(sheet.values) == [("Animal ID", "Liters"), ("T-001", 12.5), ("T-002", 0)]
    assert workbook["Summary"]["B2"].value == 2

    pdf_payload = pdf_bytes("Daily Milk Production", columns, rows, summary)
    assert pdf_payload.startswith(b"%PDF-")
    assert len(pdf_payload) > 500


def test_reporting_ui_does_not_fake_pdf_or_xlsx_with_html_blobs():
    source = REPORTING_UI.read_text(encoding="utf-8")
    assert "application/vnd.ms-excel" not in source
    assert "new Blob([printableHtml(data)]" not in source
    assert "/farm/reporting/export?format=" in source


def test_print_and_save_always_fetch_current_controls_not_cached_preview():
    source = REPORTING_UI.read_text(encoding="utf-8")
    assert "preview || await loadDataset()" not in source
    assert source.count("const data = await loadDataset()") >= 2
    assert "JSON.stringify(requestBody())" in source


def test_preview_print_and_exports_share_the_same_reporting_request_contract():
    source = REPORTING_UI.read_text(encoding="utf-8")
    assert "report_id: report.id" in source
    assert "operational_date: asOfDate" in source
    assert "snapshot_date: asOfDate" in source
    assert "body:JSON.stringify(requestBody())" in source or "body: JSON.stringify(requestBody())" in source


def test_export_contract_has_explicit_reconciliation_metadata():
    source = REPORTING_API.read_text(encoding="utf-8")
    assert "X-DairyOS-Report-Id" in source
    assert "X-DairyOS-Record-Count" in source
    assert "X-DairyOS-Dataset-Status" in source


def test_ui_rejects_export_when_preview_and_export_metadata_diverge():
    source = REPORTING_UI.read_text(encoding="utf-8")
    assert "exportedReport !== report.id" in source
    assert "exportedCount !== String(data.record_count" in source
    assert "exportedStatus !== data.dataset_status"
    assert "Report export reconciliation failed" in source


def test_semen_stock_is_not_exposed_by_reporting():
    api_source = REPORTING_API.read_text(encoding="utf-8")
    ui_source = REPORTING_UI.read_text(encoding="utf-8")
    assert '"SEMEN"' not in api_source
    assert '"semen-stock"' not in api_source
    assert "Semen Stock Balance" not in api_source
    assert "|'SEMEN'" not in ui_source
    assert "SEMEN:'Semen'" not in ui_source

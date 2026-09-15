from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTING_API = ROOT / "src" / "dairyos" / "api" / "reporting.py"
REPORTING_UI = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "ReportingTab.tsx"
PYPROJECT = ROOT / "pyproject.toml"


def test_reporting_api_exposes_canonical_export_endpoint():
    source = REPORTING_API.read_text(encoding="utf-8")
    assert '@router.post("/export")' in source
    assert "reporting_export" in source
    assert "_canonical_dataset(" in source


def test_reporting_dependencies_include_real_pdf_and_xlsx_writers():
    source = PYPROJECT.read_text(encoding="utf-8").lower()
    assert "openpyxl" in source
    assert "reportlab" in source


def test_reporting_api_generates_real_csv_xlsx_and_pdf_payloads():
    source = REPORTING_API.read_text(encoding="utf-8")
    assert "text/csv" in source
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in source
    assert "application/pdf" in source
    assert "openpyxl" in source.lower()
    assert "reportlab" in source.lower()


def test_reporting_ui_does_not_fake_pdf_or_xlsx_with_html_blobs():
    source = REPORTING_UI.read_text(encoding="utf-8")
    assert "application/vnd.ms-excel" not in source
    assert "text/html;charset=utf-8" not in source
    assert "<table><thead><tr>${columns.map" not in source


def test_print_and_save_always_fetch_current_controls_not_cached_preview():
    source = REPORTING_UI.read_text(encoding="utf-8")
    assert "preview || await loadDataset()" not in source
    assert "const data = await loadDataset()" in source
    assert "const response = await fetch(apiUrl('/farm/reporting/export')" in source


def test_preview_print_and_exports_share_the_same_reporting_request_contract():
    source = REPORTING_UI.read_text(encoding="utf-8")
    assert "JSON.stringify(requestBody())" in source
    assert "report_id: report.id" in source
    assert "operational_date: asOfDate" in source
    assert "snapshot_date: asOfDate" in source


def test_export_contract_has_explicit_reconciliation_metadata():
    source = REPORTING_API.read_text(encoding="utf-8")
    assert "X-DairyOS-Report-Id" in source
    assert "X-DairyOS-Record-Count" in source
    assert "X-DairyOS-Dataset-Status" in source

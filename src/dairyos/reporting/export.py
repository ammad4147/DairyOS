"""Typed rendering of a report result to CSV, Excel and PDF.

Every exporter receives exactly the payload the screen shows (same report,
period, filters, selected columns, totals and values), built with
``all_rows=True`` so an export is never a single page of a longer report.

* CSV and Excel favour analysis: numeric values stay numeric, dates stay
  dates, money is written as a number with a currency number format.
* PDF favours presentation: title block, parameters, summary, tables with a
  totals row, reconciliation controls and notes, on A4.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from io import BytesIO, StringIO
from typing import Any
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NUMERIC = {"integer", "number", "litres", "kg", "money", "rate", "percent", "days"}
EXCEL_FORMATS = {
    "integer": "#,##0", "days": "#,##0", "number": "#,##0.00", "litres": "#,##0.00", "kg": "#,##0.000",
    "money": "#,##0.00", "rate": "#,##0.0000", "percent": "0.0", "date": "DD-MMM-YYYY",
}
DECIMALS = {"integer": 0, "days": 0, "number": 2, "litres": 2, "kg": 3, "money": 2, "rate": 4, "percent": 1}
PDF_MARGIN = 12 * mm
BRAND = colors.HexColor("#0E5947")
RULE = colors.HexColor("#C9CFC6")
BAND = colors.HexColor("#EEF2EC")


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def display(value: Any, kind: str, *, currency: bool = True) -> str:
    """Operator presentation of one value. Never prints None or null."""
    if value is None or value == "":
        return ""
    if kind == "date":
        parsed = _parse_date(value)
        return parsed.strftime("%d-%b-%Y") if parsed else str(value)
    if kind == "datetime":
        return str(value).replace("T", " ")[:16]
    if kind in NUMERIC:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        text = f"{number:,.{DECIMALS[kind]}f}"
        if kind == "money" and currency:
            return f"PKR {text}"
        if kind == "percent":
            return f"{text}%"
        return text
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def typed(value: Any, kind: str) -> Any:
    """Analysis value: numbers stay numeric and dates stay dates."""
    if value is None or value == "":
        return None
    if kind == "date":
        return _parse_date(value) or str(value)
    if kind in NUMERIC:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        return int(number) if kind in {"integer", "days"} and number == int(number) else number
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _parameter_lines(payload: dict[str, Any]) -> list[tuple[str, str]]:
    lines = [("Report", payload["report"]["title"]), ("Period", payload["period"]["label"])]
    lines += [(item["label"], str(item["value"])) for item in payload.get("filters_applied", [])]
    lines.append(("Generated", str(payload["generated_at"]).replace("T", " ")[:16]))
    lines.append(("Authority", payload["report"]["authority"]))
    return lines


def file_stem(payload: dict[str, Any]) -> str:
    title = "".join(ch if ch.isalnum() else "-" for ch in payload["report"]["title"]).strip("-")
    while "--" in title:
        title = title.replace("--", "-")
    period = payload["period"]
    if period.get("start_date") and period.get("end_date"):
        span = f"{period['start_date']}_to_{period['end_date']}"
    else:
        span = period.get("as_of_date") or ""
    return f"DairyOS-{title}-{span}".rstrip("-")


# ---------------------------------------------------------------------------
def csv_bytes(payload: dict[str, Any], farm_name: str) -> bytes:
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(["Farm", farm_name])
    for label, value in _parameter_lines(payload):
        writer.writerow([label, value])
    for section in payload["sections"]:
        writer.writerow([])
        writer.writerow([section["title"]])
        columns = section["columns"]
        writer.writerow([column["label"] for column in columns])
        for row in section["rows"]:
            writer.writerow([_csv_value(row.get(c["key"]), c["type"]) for c in columns])
        totals = section.get("totals")
        if totals:
            line = [_csv_value(totals.get(c["key"]), c["type"]) for c in columns]
            if columns and line[0] in ("", None):
                line[0] = totals.get("_label", "Total")
            writer.writerow(line)
    return ("﻿" + stream.getvalue()).encode("utf-8")


def _csv_value(value: Any, kind: str) -> Any:
    result = typed(value, kind)
    if result is None:
        return ""
    if isinstance(result, date):
        return result.isoformat()
    if isinstance(result, float):
        return f"{result:.{DECIMALS.get(kind, 2)}f}"
    return result


# ---------------------------------------------------------------------------
def xlsx_bytes(payload: dict[str, Any], farm_name: str) -> bytes:
    workbook = Workbook()
    cover = workbook.active
    cover.title = "Report"
    bold = Font(bold=True)
    cover.append([farm_name])
    cover["A1"].font = Font(bold=True, size=14)
    for label, value in _parameter_lines(payload):
        cover.append([label, value])
        cover.cell(row=cover.max_row, column=1).font = bold
    if payload.get("summary"):
        cover.append([])
        cover.append(["Summary"])
        cover.cell(row=cover.max_row, column=1).font = bold
        for metric in payload["summary"]:
            cover.append([metric["label"], typed(metric["value"], metric["type"]), metric.get("hint")])
            cell = cover.cell(row=cover.max_row, column=2)
            if metric["type"] in EXCEL_FORMATS:
                cell.number_format = EXCEL_FORMATS[metric["type"]]
            cell.alignment = Alignment(horizontal="left")
    if payload.get("reconciliation"):
        cover.append([])
        cover.append(["Reconciliation Control", "Expected", "Actual", "Difference", "Result"])
        for cell in cover[cover.max_row]:
            cell.font = bold
        for check in payload["reconciliation"]:
            cover.append([check["check"], typed(check["expected"], check["type"]), typed(check["actual"], check["type"]),
                          typed(check["difference"], check["type"]), check["status"]])
            for index in (2, 3, 4):
                cover.cell(row=cover.max_row, column=index).number_format = EXCEL_FORMATS.get(check["type"], "General")
    if payload.get("notes"):
        cover.append([])
        cover.append(["Notes"])
        cover.cell(row=cover.max_row, column=1).font = bold
        for note in payload["notes"]:
            cover.append([note])
    cover.column_dimensions["A"].width = 44
    for letter in "BCDE":
        cover.column_dimensions[letter].width = 22

    header_fill = PatternFill("solid", fgColor="0E5947")
    total_fill = PatternFill("solid", fgColor="EEF2EC")
    top_rule = Border(top=Side(style="thin", color="18211D"))
    used_titles = {"Report"}
    for section in payload["sections"]:
        title = "".join(ch for ch in section["title"] if ch not in '[]:*?/\\')[:31] or "Data"
        base, counter = title, 2
        while title in used_titles:
            title = f"{base[:28]} {counter}"
            counter += 1
        used_titles.add(title)
        sheet = workbook.create_sheet(title)
        columns = section["columns"]
        sheet.append([column["label"] for column in columns])
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        for row in section["rows"]:
            sheet.append([typed(row.get(c["key"]), c["type"]) for c in columns])
        totals = section.get("totals")
        if totals:
            line = [typed(totals.get(c["key"]), c["type"]) for c in columns]
            if columns and line[0] is None:
                line[0] = totals.get("_label", "Total")
            sheet.append(line)
            for cell in sheet[sheet.max_row]:
                cell.font, cell.fill, cell.border = bold, total_fill, top_rule
        for index, column in enumerate(columns, start=1):
            letter = get_column_letter(index)
            number_format = EXCEL_FORMATS.get(column["type"])
            longest = len(column["label"])
            for cell in sheet[letter][1:]:
                if number_format:
                    cell.number_format = number_format
                    cell.alignment = Alignment(horizontal="right")
                longest = max(longest, len(display(cell.value, column["type"], currency=False)))
            sheet.column_dimensions[letter].width = min(48, max(10, longest + 3))
        sheet.freeze_panes = "A2"
        if columns and section["rows"]:
            sheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(section['rows']) + 1}"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


# ---------------------------------------------------------------------------
def pdf_bytes(payload: dict[str, Any], farm_name: str) -> bytes:
    widest = max((len(section["columns"]) for section in payload["sections"]), default=0)
    page_size = landscape(A4) if widest > 7 else portrait(A4)
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=page_size, leftMargin=PDF_MARGIN, rightMargin=PDF_MARGIN,
                                 topMargin=PDF_MARGIN, bottomMargin=14 * mm, title=payload["report"]["title"],
                                 author=farm_name)
    base = getSampleStyleSheet()["BodyText"]
    title_style = ParagraphStyle("T", parent=base, fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=BRAND)
    farm_style = ParagraphStyle("F", parent=base, fontName="Helvetica-Bold", fontSize=10, leading=12)
    meta_style = ParagraphStyle("M", parent=base, fontSize=8.5, leading=11, textColor=colors.HexColor("#39443E"))
    heading_style = ParagraphStyle("H", parent=base, fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=6)
    note_style = ParagraphStyle("N", parent=base, fontSize=8, leading=10.5, textColor=colors.HexColor("#39443E"))
    cell_size = 7.2 if widest > 10 else 8
    head = ParagraphStyle("CH", parent=base, fontName="Helvetica-Bold", fontSize=cell_size, leading=cell_size + 1.8, textColor=colors.white)
    left = ParagraphStyle("CL", parent=base, fontSize=cell_size, leading=cell_size + 1.8)
    right = ParagraphStyle("CR", parent=left, alignment=2)
    left_bold = ParagraphStyle("CLB", parent=left, fontName="Helvetica-Bold")
    right_bold = ParagraphStyle("CRB", parent=right, fontName="Helvetica-Bold")

    story: list[Any] = [Paragraph(escape(farm_name), farm_style), Paragraph(escape(payload["report"]["title"]), title_style)]
    meta = " &nbsp;|&nbsp; ".join(f"<b>{escape(label)}:</b> {escape(value)}" for label, value in _parameter_lines(payload)[1:-1])
    story += [Paragraph(meta, meta_style), Spacer(1, 3 * mm)]

    if payload.get("summary"):
        cells = [[Paragraph(f"<font size=7 color='#69736D'>{escape(m['label'].upper())}</font><br/>"
                            f"<b>{escape(display(m['value'], m['type']) or 'Not available')}</b>", left)
                  for m in payload["summary"][:6]]]
        table = Table(cells, colWidths=[(page_size[0] - 2 * PDF_MARGIN) / len(cells[0])] * len(cells[0]))
        table.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, RULE), ("INNERGRID", (0, 0), (-1, -1), 0.5, RULE),
                                   ("BACKGROUND", (0, 0), (-1, -1), BAND), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story += [table, Spacer(1, 3 * mm)]

    available = page_size[0] - 2 * PDF_MARGIN
    for section in payload["sections"]:
        story.append(Paragraph(escape(section["title"]), heading_style))
        if section.get("note"):
            story.append(Paragraph(escape(section["note"]), note_style))
        columns = section["columns"]
        if not section["rows"]:
            story += [Paragraph(escape(section.get("empty_message") or "No records match the selected parameters."), note_style),
                      Spacer(1, 2 * mm)]
            continue
        data = [[Paragraph(escape(c["label"]), head) for c in columns]]
        for row in section["rows"]:
            strong = row.get("_emphasis") == "total"
            data.append([Paragraph(escape(display(row.get(c["key"]), c["type"], currency=False)),
                                   (right_bold if strong else right) if c["type"] in NUMERIC else (left_bold if strong else left))
                         for c in columns])
        totals = section.get("totals")
        if totals:
            line = []
            for index, c in enumerate(columns):
                text = display(totals.get(c["key"]), c["type"], currency=False)
                if index == 0 and not text:
                    text = totals.get("_label", "Total")
                line.append(Paragraph(escape(text), right_bold if c["type"] in NUMERIC else left_bold))
            data.append(line)
        weights = []
        for c in columns:
            longest = max([len(c["label"])] + [len(display(r.get(c["key"]), c["type"], currency=False)) for r in section["rows"][:200]])
            weights.append(max(6, min(30, longest)))
        widths = [available * w / sum(weights) for w in weights]
        table = Table(data, repeatRows=1, colWidths=widths)
        style = [("BACKGROUND", (0, 0), (-1, 0), BRAND), ("LINEBELOW", (0, 0), (-1, -1), 0.25, RULE),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                 ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAF7")])]
        if totals:
            style += [("BACKGROUND", (0, -1), (-1, -1), BAND), ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor("#18211D"))]
        table.setStyle(TableStyle(style))
        story += [table, Spacer(1, 3 * mm)]

    if payload.get("reconciliation"):
        story.append(Paragraph("Reconciliation Controls", heading_style))
        data = [[Paragraph(t, head) for t in ("Control", "Expected", "Actual", "Difference", "Result")]]
        for check in payload["reconciliation"]:
            data.append([Paragraph(escape(check["check"]), left)]
                        + [Paragraph(escape(display(check[k], check["type"])), right) for k in ("expected", "actual", "difference")]
                        + [Paragraph(escape(check["status"]), left_bold)])
        table = Table(data, colWidths=[available * w for w in (0.44, 0.15, 0.15, 0.15, 0.11)])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BRAND), ("LINEBELOW", (0, 0), (-1, -1), 0.25, RULE),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story += [table, Spacer(1, 3 * mm)]

    if payload.get("notes"):
        story.append(Paragraph("Notes", heading_style))
        story += [Paragraph("• " + escape(note), note_style) for note in payload["notes"]]
    story += [Spacer(1, 2 * mm), Paragraph(f"<b>Authority:</b> {escape(payload['report']['authority'])}", note_style)]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#69736D"))
        canvas.drawString(PDF_MARGIN, 8 * mm, f"{farm_name}  |  {payload['report']['title']}  |  {payload['period']['label']}")
        canvas.drawRightString(page_size[0] - PDF_MARGIN, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()

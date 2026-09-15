"""Binary exporters for the governed DairyOS Reporting dataset."""

from __future__ import annotations

import csv
import json
from io import BytesIO, StringIO
from typing import Any

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def csv_bytes(columns: list[str], rows: list[dict[str, Any]]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_cell(row.get(column)) for column in columns])
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def xlsx_bytes(
    title: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Report"
    sheet.append(columns)
    for row in rows:
        sheet.append([_cell(row.get(column)) for column in columns])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cells in sheet.columns:
        width = min(60, max(10, max(len(_cell(cell.value)) for cell in cells) + 2))
        sheet.column_dimensions[cells[0].column_letter].width = width

    meta = workbook.create_sheet("Summary")
    meta.append(["DairyOS Report", title])
    meta.append(["Record Count", len(rows)])
    for key, value in summary.items():
        meta.append([str(key), _cell(value)])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def pdf_bytes(
    title: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(f"DairyOS — {title}", styles["Title"]), Spacer(1, 4 * mm)]
    if summary:
        summary_text = " · ".join(f"{key}: {_cell(value)}" for key, value in summary.items())
        story.extend([Paragraph(summary_text, styles["BodyText"]), Spacer(1, 3 * mm)])

    if columns:
        data = [[Paragraph(str(column), styles["BodyText"]) for column in columns]]
        for row in rows:
            data.append([Paragraph(_cell(row.get(column)), styles["BodyText"]) for column in columns])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No records match the selected report controls.", styles["BodyText"]))

    document.build(story)
    return output.getvalue()

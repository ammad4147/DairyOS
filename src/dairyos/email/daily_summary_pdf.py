from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

NAVY = colors.HexColor("#0B376D")
GREEN = colors.HexColor("#27863A")
ORANGE = colors.HexColor("#F36A16")
PURPLE = colors.HexColor("#575184")
RED = colors.HexColor("#C9151E")
LIGHT = colors.HexColor("#F4F8FB")
RULE = colors.HexColor("#D5E0E8")
TEXT = colors.HexColor("#12294A")


def _money(value: Any, decimals: int = 2) -> str:
    return f"PKR {float(value or 0):,.{decimals}f}"


def _num(value: Any, decimals: int = 1) -> str:
    return f"{float(value or 0):,.{decimals}f}"


def _box(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, accent) -> None:
    c.setFillColor(colors.white)
    c.setStrokeColor(RULE)
    c.roundRect(x, y, w, h, 3 * mm, fill=1, stroke=1)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 10 * mm, w, 10 * mm, 3 * mm, fill=1, stroke=0)
    c.rect(x, y + h - 5 * mm, w, 5 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 4 * mm, y + h - 6.7 * mm, title)


def _row(c: canvas.Canvas, x: float, y: float, label: str, value: str, width: float, bold: bool = False) -> None:
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", 7.5)
    c.drawString(x, y, label)
    c.drawRightString(x + width, y, value)


def daily_summary_pdf(summary: dict[str, Any]) -> bytes:
    """Render the governed daily-summary payload as exactly one A4 page."""
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4, pageCompression=1)
    width, height = A4
    margin = 9 * mm
    usable = width - 2 * margin
    date_value = summary.get("operational_date")
    if isinstance(date_value, date):
        date_text = date_value.strftime("%d %B %Y")
    else:
        try:
            date_text = date.fromisoformat(str(date_value)).strftime("%d %B %Y")
        except ValueError:
            date_text = str(date_value)

    c.setTitle(f"DairyOS Daily Farm Summary - {date_text}")
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin, height - 17 * mm, "DairyOS")
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(width / 2, height - 15 * mm, "DAILY FARM SUMMARY")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 22 * mm, date_text)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, height - 27 * mm, "Operational Day")

    milk = summary["milk"]
    herd = summary["herd"]
    cop = summary["cop"]
    finance = summary.get("finance") or {}
    health = summary.get("health") or {}
    attention = summary.get("attention") or []
    milking = int(herd["counts"].get("Milking", 0) or 0)
    yield_l = float(milk.get("total_yield") or 0)
    per_cow = yield_l / milking if milking else 0
    net_cash = float(finance.get("revenue_received") or 0) - float(finance.get("expenses") or 0)

    y = height - 39 * mm
    c.setFillColor(colors.HexColor("#EAF5EC"))
    c.roundRect(margin, y - 30 * mm, usable, 30 * mm, 3 * mm, fill=1, stroke=0)
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin + 4 * mm, y - 6 * mm, "TODAY AT A GLANCE")
    cards = [
        ("MILK PRODUCED", f"{_num(yield_l)} L", f"{_num(per_cow)} L / milking cow", NAVY),
        ("HERD", f"{herd['total']} head", f"{milking} milking cows", GREEN),
        ("COST OF PRODUCTION", f"{_money(cop.get('total_cop_per_liter'))} / L", f"Feed {_num(cop.get('feed_cost_per_liter'), 2)} / L", ORANGE),
        ("CASH MOVEMENT", _money(net_cash), f"Receipts {_money(finance.get('revenue_received'))}", PURPLE),
        ("ATTENTION", f"{len(attention)} item" + ("" if len(attention) == 1 else "s"), f"Health {health.get('active_exceptions', 0)}", RED),
    ]
    card_w = usable / 5
    for i, (label, value, hint, accent) in enumerate(cards):
        x = margin + i * card_w
        if i:
            c.setStrokeColor(colors.HexColor("#C9D9E1")); c.line(x, y - 27 * mm, x, y - 9 * mm)
        c.setFillColor(accent); c.setFont("Helvetica-Bold", 7); c.drawString(x + 3 * mm, y - 13 * mm, label)
        c.setFillColor(TEXT); c.setFont("Helvetica-Bold", 11); c.drawString(x + 3 * mm, y - 20 * mm, value[:25])
        c.setFont("Helvetica", 6.5); c.drawString(x + 3 * mm, y - 25 * mm, hint[:32])

    gap = 4 * mm
    col_w = (usable - gap) / 2
    top = y - 35 * mm
    h1 = 67 * mm
    _box(c, margin, top - h1, col_w, h1, "MILK PRODUCTION & UTILIZATION", NAVY)
    _box(c, margin + col_w + gap, top - h1, col_w, h1, "HERD STATUS & TODAY'S ACTIVITY", GREEN)
    ry = top - 17 * mm
    rows = [
        ("Total Milk Produced", f"{_num(yield_l)} L"),
        ("Per Milking Cow", f"{_num(per_cow)} L"),
        ("Milk Sold", f"{_num(milk.get('sold'))} L"),
        ("Calf Feed", f"{_num(milk.get('calf_feed'))} L"),
        ("Domestic Use", f"{_num(milk.get('domestic_use'))} L"),
        ("Wastage", f"{_num(milk.get('wastage'))} L"),
        ("Unaccounted", f"{_num(milk.get('unaccounted'))} L"),
        ("Yield Drop Alerts", str(len(milk.get("watchlist") or []))),
    ]
    for label, value in rows:
        _row(c, margin + 4 * mm, ry, label, value, col_w - 8 * mm, label in {"Total Milk Produced", "Unaccounted"}); ry -= 5.2 * mm

    ry = top - 17 * mm
    counts = herd["counts"]
    for label, key in [("Milking Cows","Milking"),("Dry Cows","Dry"),("Heifers","Heifer"),("Female Calves","Female Calf"),("Male Calves","Male Calf"),("Bulls","Bull"),("Total Herd",None)]:
        value = herd["total"] if key is None else counts.get(key, 0)
        _row(c, margin + col_w + gap + 4 * mm, ry, label, str(value), col_w - 8 * mm, key is None); ry -= 5.2 * mm
    _row(c, margin + col_w + gap + 4 * mm, ry, "Deaths Today", str(len(herd.get("mortalities") or [])), col_w - 8 * mm)

    top2 = top - h1 - gap
    h2 = 53 * mm
    _box(c, margin, top2 - h2, col_w, h2, "FEED & COST OF PRODUCTION", ORANGE)
    _box(c, margin + col_w + gap, top2 - h2, col_w, h2, "FINANCIAL SNAPSHOT (CASH BASIS)", PURPLE)
    ry = top2 - 18 * mm
    total_cop = float(cop.get("feed_total") or 0) + float(cop.get("opex_total") or 0)
    for label, value in [
        ("Feed Cost", _money(cop.get("feed_total"))),
        ("Feed Cost / L", _money(cop.get("feed_cost_per_liter"))),
        ("Operating Expenses", _money(cop.get("opex_total"))),
        ("OPEX / L", _money(cop.get("opex_cost_per_liter"))),
        ("Total COP", _money(total_cop)),
        ("Total COP / L", _money(cop.get("total_cop_per_liter"))),
    ]:
        _row(c, margin + 4 * mm, ry, label, value, col_w - 8 * mm, label.startswith("Total COP")); ry -= 5.2 * mm

    ry = top2 - 18 * mm
    for label, value in [
        ("Receipts", _money(finance.get("revenue_received"))),
        ("Payments / Expenses", _money(finance.get("expenses"))),
        ("Net Cash Movement", _money(net_cash)),
    ]:
        _row(c, margin + col_w + gap + 4 * mm, ry, label, value, col_w - 8 * mm, label == "Net Cash Movement"); ry -= 7 * mm

    top3 = top2 - h2 - gap
    h3 = 30 * mm
    _box(c, margin, top3 - h3, col_w, h3, "REPRODUCTION", colors.HexColor("#C96882"))
    _box(c, margin + col_w + gap, top3 - h3, col_w, h3, "HEALTH & WELFARE", colors.HexColor("#DF3A32"))
    reproduction = summary.get("reproduction")
    c.setFillColor(TEXT); c.setFont("Helvetica", 7.5)
    if reproduction:
        c.drawString(margin + 4 * mm, top3 - 18 * mm, f"AI {reproduction.get('ai', 0)}   PD {reproduction.get('pd', 0)}   Confirmed {reproduction.get('confirmed', 0)}   Losses {reproduction.get('losses', 0)}   Due {reproduction.get('due', 0)}")
    else:
        c.drawString(margin + 4 * mm, top3 - 18 * mm, "Reproductive activity: see governed Breeding records")
    c.drawString(margin + col_w + gap + 4 * mm, top3 - 18 * mm, f"Active Health Alerts: {health.get('active_exceptions', 0)}")
    c.drawString(margin + col_w + gap + 4 * mm, top3 - 24 * mm, f"Under Milk Withdrawal: {health.get('withdrawal_count', 0)}")

    top4 = top3 - h3 - gap
    h4 = 35 * mm
    _box(c, margin, top4 - h4, usable, h4, "ATTENTION REQUIRED", RED)
    c.setFillColor(TEXT); c.setFont("Helvetica-Bold", 8)
    if not attention:
        c.drawString(margin + 4 * mm, top4 - 18 * mm, "No outstanding operational warnings.")
    else:
        max_rows = 3
        c.drawString(margin + 4 * mm, top4 - 17 * mm, f"{len(attention)} item(s) require attention")
        c.setFont("Helvetica", 7)
        yy = top4 - 23 * mm
        for item in attention[:max_rows]:
            subject = f" [{item.get('subject_id')}]" if item.get("subject_id") else ""
            severity = str(item.get("severity") or "INFO").upper()
            line = f"{severity} | {item.get('area','Operational')}{subject}: {item.get('title','Action required')}"
            c.drawString(margin + 5 * mm, yy, line[:115]); yy -= 5 * mm
        if len(attention) > max_rows:
            c.drawRightString(width - margin - 4 * mm, top4 - 31 * mm, f"+ {len(attention)-max_rows} more in DairyOS")

    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, 8 * mm, f"DairyOS  |  Governed records for {date_text}")
    c.setStrokeColor(GREEN); c.line(margin, 6 * mm, width - margin, 6 * mm)
    c.showPage()
    c.save()
    return output.getvalue()

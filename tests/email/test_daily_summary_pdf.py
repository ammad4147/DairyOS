from __future__ import annotations

from datetime import date
from dairyos.email.daily_summary_pdf import daily_summary_pdf
from dairyos.email.service import EmailSenderConfig, EmailService


def _summary(**overrides):
    value = {
        "operational_date": date(2026, 9, 20),
        "milk": {
            "total_yield": 135.0,
            "sold": 135.0,
            "calf_feed": 0.0,
            "domestic_use": 0.0,
            "wastage": 0.0,
            "unaccounted": 0.0,
            "watchlist": [],
        },
        "herd": {
            "total": 4,
            "counts": {
                "Milking": 3,
                "Dry": 0,
                "Heifer": 0,
                "Female Calf": 1,
                "Male Calf": 0,
                "Bull": 0,
            },
            "mortalities": [],
        },
        "cop": {
            "feed_total": 5431.20,
            "feed_cost_per_liter": 40.23,
            "opex_total": 6666.67,
            "opex_cost_per_liter": 49.38,
            "total_cop_per_liter": 89.61,
        },
        "finance": {"revenue_received": 33750.0, "expenses": 330350.0},
        "health": {"active_exceptions": 1, "withdrawal_count": 0},
        "reproduction": {"ai": 0, "pd": 0, "confirmed": 0, "losses": 0, "calvings": 0, "due": 0},
        "attention": [],
    }
    value.update(overrides)
    return value


def test_daily_summary_pdf_is_exactly_one_page_and_contains_governed_values():
    payload = daily_summary_pdf(_summary())
    assert payload.startswith(b"%PDF-")
    assert payload.count(b"/Type /Page") == 1


def test_daily_summary_pdf_caps_attention_rows_without_overflow():
    attention = [
        {"area": "Health", "title": f"Finding {index}"}
        for index in range(10)
    ]
    payload = daily_summary_pdf(_summary(attention=attention))
    assert payload.startswith(b"%PDF-")
    assert payload.count(b"/Type /Page") == 1


def test_email_service_adds_pdf_attachment(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            captured["host"] = host
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def starttls(self):
            pass
        def login(self, username, password):
            pass
        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr("dairyos.email.service.smtplib.SMTP", FakeSMTP)
    service = EmailService()
    service.send(
        recipient="manager@example.com",
        subject="DairyOS Daily Summary",
        body="Summary attached.",
        config=EmailSenderConfig(
            host="smtp.example.com",
            port=587,
            username="user",
            password="secret",
            from_address="dairyos@example.com",
        ),
        attachments=[("DairyOS-Daily-Summary-2026-09-20.pdf", b"%PDF-test", "application", "pdf")],
    )

    attachments = list(captured["message"].iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "DairyOS-Daily-Summary-2026-09-20.pdf"
    assert attachments[0].get_content_type() == "application/pdf"

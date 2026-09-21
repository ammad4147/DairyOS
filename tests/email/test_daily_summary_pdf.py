from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from dairyos.email.daily_summary_pdf import daily_summary_pdf
from dairyos.email.digest import DashboardDigestService
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
    assert payload.count(b"/Type /Page") - payload.count(b"/Type /Pages") == 1


def test_daily_summary_pdf_caps_attention_rows_without_overflow():
    attention = [
        {"area": "Health", "title": f"Finding {index}"}
        for index in range(10)
    ]
    payload = daily_summary_pdf(_summary(attention=attention))
    assert payload.startswith(b"%PDF-")
    assert payload.count(b"/Type /Page") - payload.count(b"/Type /Pages") == 1


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
            sender_email="dairyos@example.com",
            sender_display_name="DairyOS",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="secret",
            use_tls=True,
        ),
        attachments=[("DairyOS-Daily-Summary-2026-09-20.pdf", b"%PDF-test", "application", "pdf")],
    )

    attachments = list(captured["message"].iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "DairyOS-Daily-Summary-2026-09-20.pdf"
    assert attachments[0].get_content_type() == "application/pdf"


def test_delivery_content_reports_incomplete_status_and_attention():
    service = DashboardDigestService(
        container=SimpleNamespace(repository_factory=SimpleNamespace())
    )
    summary = _summary(
        completeness={"status": "INCOMPLETE"},
        attention=[{"area": "Milk", "title": "Session missing"}],
    )
    subject, body = service._delivery_content(summary)
    assert "1 attention item(s)" in subject
    assert "Data status: Incomplete" in body
    assert "Milk produced: 135.0 L" in body


def test_pdf_accepts_restricted_finance_and_unavailable_authorities():
    summary = _summary(
        finance=None,
        cop={
            "feed_total": None,
            "feed_cost_per_liter": None,
            "opex_total": None,
            "opex_cost_per_liter": None,
            "total_cop_per_liter": None,
        },
        health={"active_exceptions": None},
        completeness={"status": "INCOMPLETE"},
    )
    payload = daily_summary_pdf(summary)
    assert payload.startswith(b"%PDF-")
    assert payload.count(b"/Type /Page") - payload.count(b"/Type /Pages") == 1


class _CompletenessFactory:
    def __init__(self, sessions, feed_records):
        self.sessions = sessions
        self.feed_records = feed_records

    def milking_session_ledger(self):
        return SimpleNamespace(
            settled_sessions_on=lambda ignored: set(self.sessions)
        )

    def feed(self):
        return SimpleNamespace(get_all=lambda: list(self.feed_records))

    def close(self):
        return None


def test_daily_completeness_requires_three_sessions_five_feeds_and_tmr(monkeypatch):
    factory = _CompletenessFactory(
        {"MORNING", "AFTERNOON", "EVENING"},
        [
            SimpleNamespace(
                feeding_date=datetime(2026, 9, 20, hour, tzinfo=UTC)
            )
            for hour in (1, 3, 5, 7, 9)
        ],
    )
    monkeypatch.setattr(
        "dairyos.email.digest.RepositoryFactory.create",
        lambda: factory,
    )
    service = DashboardDigestService(
        container=SimpleNamespace(repository_factory=SimpleNamespace())
    )
    service._farm_timezone = lambda fallback=None: UTC
    result = service._daily_completeness(
        digest_date=date(2026, 9, 20),
        cop={"feed_complete": True},
    )
    assert result["status"] == "COMPLETE"
    assert result["missing_milk_sessions"] == []
    assert result["feed_event_count"] == 5


def test_daily_completeness_identifies_missing_session_and_feed(monkeypatch):
    factory = _CompletenessFactory(
        {"MORNING", "EVENING"},
        [
            SimpleNamespace(
                feeding_date=datetime(2026, 9, 20, hour, tzinfo=UTC)
            )
            for hour in (1, 3, 5, 7)
        ],
    )
    monkeypatch.setattr(
        "dairyos.email.digest.RepositoryFactory.create",
        lambda: factory,
    )
    service = DashboardDigestService(
        container=SimpleNamespace(repository_factory=SimpleNamespace())
    )
    service._farm_timezone = lambda fallback=None: UTC
    result = service._daily_completeness(
        digest_date=date(2026, 9, 20),
        cop={"feed_complete": False},
    )
    assert result["status"] == "INCOMPLETE"
    assert result["missing_milk_sessions"] == ["AFTERNOON"]
    assert result["feed_event_count"] == 4
    assert result["checks"]["tmr_authority"] is False


def test_zero_milk_is_preserved_as_governed_zero():
    summary = _summary(
        milk={
            "total_yield": 0.0,
            "sold": 0.0,
            "calf_feed": 0.0,
            "domestic_use": 0.0,
            "wastage": 0.0,
            "unaccounted": 0.0,
            "watchlist": [],
        },
        completeness={"status": "COMPLETE"},
    )
    payload = daily_summary_pdf(summary)
    assert payload.startswith(b"%PDF-")
    assert payload.count(b"/Type /Page") - payload.count(b"/Type /Pages") == 1


def test_missing_milk_authority_is_not_treated_as_zero():
    service = DashboardDigestService(
        container=SimpleNamespace(repository_factory=SimpleNamespace())
    )
    summary = _summary(
        milk={
            "total_yield": None,
            "sold": 0.0,
            "calf_feed": 0.0,
            "domestic_use": 0.0,
            "wastage": 0.0,
            "unaccounted": 0.0,
            "watchlist": [],
        },
        completeness={"status": "INCOMPLETE"},
    )
    subject, body = service._delivery_content(summary)
    assert subject.startswith("DairyOS Daily Summary")
    assert "Milk produced: Unavailable" in body
    payload = daily_summary_pdf(summary)
    assert payload.startswith(b"%PDF-")
    assert payload.count(b"/Type /Page") - payload.count(b"/Type /Pages") == 1


def test_feed_event_on_utc_previous_day_counts_on_farm_operational_day(monkeypatch):
    from zoneinfo import ZoneInfo

    factory = _CompletenessFactory(
        {"MORNING", "AFTERNOON", "EVENING"},
        [
            SimpleNamespace(
                feeding_date=datetime(2026, 9, 19, 20, 30, tzinfo=UTC)
            )
        ],
    )
    monkeypatch.setattr(
        "dairyos.email.digest.RepositoryFactory.create",
        lambda: factory,
    )
    service = DashboardDigestService(
        container=SimpleNamespace(repository_factory=SimpleNamespace())
    )
    service._farm_timezone = lambda fallback=None: ZoneInfo("Asia/Karachi")
    result = service._daily_completeness(
        digest_date=date(2026, 9, 20),
        cop={"feed_complete": True},
    )
    assert result["feed_event_count"] == 1


def test_naive_utc_feed_event_uses_farm_operational_date(monkeypatch):
    from zoneinfo import ZoneInfo

    factory = _CompletenessFactory(
        {"MORNING", "AFTERNOON", "EVENING"},
        [SimpleNamespace(feeding_date=datetime(2026, 9, 19, 20, 30))],
    )
    monkeypatch.setattr(
        "dairyos.email.digest.RepositoryFactory.create",
        lambda: factory,
    )
    service = DashboardDigestService(
        container=SimpleNamespace(repository_factory=SimpleNamespace())
    )
    service._farm_timezone = lambda fallback=None: ZoneInfo("Asia/Karachi")
    result = service._daily_completeness(
        digest_date=date(2026, 9, 20),
        cop={"feed_complete": True},
    )
    assert result["feed_event_count"] == 1


def test_active_findings_prioritize_urgent_severity(monkeypatch):
    findings = [
        SimpleNamespace(source_module="health", subject_id="COW-LOW", severity="LOW", title="Low"),
        SimpleNamespace(source_module="milk", subject_id="COW-CRIT", severity="CRITICAL", title="Critical"),
        SimpleNamespace(source_module="breeding", subject_id="COW-HIGH", severity="HIGH", title="High"),
        SimpleNamespace(source_module="feed", subject_id="COW-WARN", severity="WARNING", title="Warning"),
    ]
    factory = SimpleNamespace(
        operational_findings=lambda: SimpleNamespace(get_open=lambda: findings),
        close=lambda: None,
    )
    monkeypatch.setattr("dairyos.email.digest.RepositoryFactory.create", lambda: factory)
    service = DashboardDigestService(
        container=SimpleNamespace(repository_factory=SimpleNamespace())
    )

    result = service._active_findings()

    assert [item["severity"] for item in result] == [
        "CRITICAL",
        "HIGH",
        "WARNING",
        "LOW",
    ]


def test_daily_summary_pdf_text_is_searchable_without_ocr():
    payload = daily_summary_pdf(
        _summary(
            milk={
                "total_yield": 135.0,
                "session_totals": {
                    "MORNING": 45.0,
                    "AFTERNOON": 44.0,
                    "EVENING": 46.0,
                },
                "sold": 135.0,
                "calf_feed": 0.0,
                "domestic_use": 0.0,
                "wastage": 0.0,
                "unaccounted": 0.0,
                "watchlist": [],
            },
            completeness={"status": "COMPLETE"},
        )
    )

    # ReportLab emits literal text-showing operators when page compression is
    # disabled. This certifies that the report contains selectable/searchable
    # PDF text rather than a rasterized page.
    assert b"(DAILY FARM SUMMARY)" in payload
    assert b"(Total Milk Produced)" in payload
    assert b"(45.0 L / 44.0 L / 46.0 L)" in payload


def test_exception_heavy_daily_summary_remains_one_a4_page():
    attention = [
        {
            "area": "HealthAndOperationalExceptionAreaWithLongName",
            "subject_id": f"ANIMAL-WITH-A-VERY-LONG-IDENTIFIER-{index:03d}",
            "severity": "CRITICAL" if index < 4 else "WARNING",
            "title": (
                "Exception title deliberately made very long to certify "
                "bounded one-page rendering without adding another page "
                f"{index}"
            ),
        }
        for index in range(40)
    ]
    payload = daily_summary_pdf(
        _summary(
            milk={
                "total_yield": 987654321.9,
                "session_totals": {
                    "MORNING": 329218107.3,
                    "AFTERNOON": 329218107.3,
                    "EVENING": 329218107.3,
                },
                "sold": 987650000.0,
                "calf_feed": 1234.5,
                "domestic_use": 987.6,
                "wastage": 432.1,
                "unaccounted": 1667.7,
                "watchlist": list(range(250)),
            },
            herd={
                "total": 999999,
                "counts": {
                    "Milking": 888888,
                    "Dry": 11111,
                    "Heifer": 22222,
                    "Female Calf": 33333,
                    "Male Calf": 44444,
                    "Bull": 555,
                },
                "mortalities": list(range(123)),
            },
            finance={
                "revenue_received": 987654321098.76,
                "expenses": 876543210987.65,
            },
            attention=attention,
            completeness={"status": "INCOMPLETE"},
        )
    )

    assert payload.startswith(b"%PDF-")
    assert payload.count(b"/Type /Page") - payload.count(b"/Type /Pages") == 1
    assert b"(40 item\(s\) require attention)" in payload
    assert b"(+ 37 more in DairyOS)" in payload

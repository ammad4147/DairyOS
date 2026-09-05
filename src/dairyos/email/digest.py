from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
import json
from zoneinfo import ZoneInfo

from dairyos.auth.permissions import permissions_from_json
from dairyos.core.time_utils import utcnow
from dairyos.dashboard.services.dashboard_projection_service import DashboardProjectionService
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.email.service import EmailService


LOCAL_ZONE = ZoneInfo("Asia/Karachi")


def _local_now() -> datetime:
    return utcnow().replace(tzinfo=ZoneInfo("UTC")).astimezone(LOCAL_ZONE)


def expected_digest_date(now: datetime | None = None) -> date:
    current = now or _local_now()
    if current.time() >= time(23, 0):
        return current.date()
    return current.date() - timedelta(days=1)


def _money(value: Decimal | float | int) -> str:
    return f"PKR {float(value):,.2f}"


class DashboardDigestService:
    """Build and deliver a permission-filtered nightly Dashboard digest."""

    def __init__(self, *, container):
        self.container = container
        self.mail = EmailService()

    def _dashboard(self) -> dict:
        service = DashboardProjectionService()
        return service.project_compatibility_dashboard_from_container(self.container)

    def _financial_snapshot(self, digest_date: date) -> dict:
        factory = RepositoryFactory.create()
        try:
            records = [
                x for x in factory.finance().get_all()
                if getattr(x, "transaction_date", None)
                and getattr(x.transaction_date, "date", lambda: x.transaction_date)() == digest_date
            ]
            active = [x for x in records if classifier.is_active(x)]
            revenue = sum(float(x.amount or 0) for x in active if classifier.is_income(x))
            expenses = sum(float(x.amount or 0) for x in active if classifier.is_expense(x))
            return {
                "revenue": revenue,
                "expenses": expenses,
                "net": revenue - expenses,
                "count": len(active),
            }
        finally:
            factory.close()

    def render(self, *, digest_date: date, user_permissions: set[str]) -> tuple[str, str]:
        dashboard = self._dashboard()
        milk = dashboard.get("milk", {})
        animals = dashboard.get("animals", {})
        health = dashboard.get("health", {})
        alerts = dashboard.get("heads_up_notifications", []) or []
        decisions = dashboard.get("operational_decisions", []) or []
        exceptions = dashboard.get("exceptions", []) or []

        subject = f"DairyOS Daily Summary — {digest_date.isoformat()}"
        lines = [subject, "", "MILK PRODUCTION"]
        litres = milk.get("today_litres")
        change = milk.get("change_percent")
        lines.append(f"Total yield today: {litres if litres is not None else 'No recorded production'} litres")
        if change is not None:
            lines.append(f"Change vs previous recorded day: {change}%")
        lines += [
            "",
            "HERD STATUS",
            f"Total headcount: {animals.get('total', 0)}",
            f"Milking animals: {animals.get('milking', 0)}",
            f"Dry animals: {animals.get('dry', 0)}",
            f"Active health exceptions: {health.get('active_exceptions', 0)}",
        ]

        if "finance.view" in user_permissions or "dashboard.view_finance" in user_permissions:
            finance = self._financial_snapshot(digest_date)
            lines += [
                "",
                "FINANCIAL SNAPSHOT",
                f"Revenue today: {_money(finance['revenue'])}",
                f"Expenses today: {_money(finance['expenses'])}",
                f"Net movement today: {_money(finance['net'])}",
            ]

        lines += ["", "ALERTS & PENDING ACTIONS"]
        items = alerts + decisions + exceptions
        if not items:
            lines.append("No active dashboard alerts or pending operational findings.")
        else:
            for item in items[:5]:
                if isinstance(item, dict):
                    title = item.get("title") or item.get("message") or item.get("type") or "Operational alert"
                    lines.append(f"- {title}")
                else:
                    lines.append(f"- {item}")

        lines += [
            "",
            "This digest reflects the latest persisted DairyOS data available when it was generated. A catch-up digest may therefore reflect the last time the system was online rather than exactly 11 PM.",
        ]
        return subject, "\n".join(lines)

    def send_for_date(self, digest_date: date) -> dict:
        factory = RepositoryFactory.create()
        try:
            run = factory.session.query(__import__("dairyos.data.models.email_digest_run", fromlist=["EmailDigestRun"]).EmailDigestRun).filter_by(digest_date=digest_date).first()
            scheduled = datetime.combine(digest_date, time(23, 0))
            EmailDigestRun = __import__("dairyos.data.models.email_digest_run", fromlist=["EmailDigestRun"]).EmailDigestRun
            EmailDigestDelivery = __import__("dairyos.data.models.email_digest_delivery", fromlist=["EmailDigestDelivery"]).EmailDigestDelivery
            if run is None:
                run = EmailDigestRun(digest_date=digest_date, scheduled_at=scheduled, status="RUNNING", generated_at=utcnow())
                factory.session.add(run)
                factory.session.commit()
                factory.session.refresh(run)
            elif run.status == "COMPLETED":
                return {"status": "already-completed", "digest_date": digest_date.isoformat(), "run_id": run.id}

            users = [u for u in factory.users().get_all() if u.active and u.personal_email]
            configured_recipients = []
            raw_recipients = factory.app_settings().get("email_notification_recipients")
            if raw_recipients:
                try:
                    parsed_recipients = json.loads(str(raw_recipients))
                except (TypeError, ValueError, json.JSONDecodeError):
                    parsed_recipients = []
                if isinstance(parsed_recipients, list):
                    configured_recipients = [
                        item for item in parsed_recipients
                        if isinstance(item, dict) and str(item.get("email") or "").strip()
                    ]
            config = self.mail.get_config()
            if config is None:
                run.status = "FAILED"
                run.completed_at = utcnow()
                factory.session.commit()
                raise RuntimeError("DairyOS email sender is not configured")

            delivered = 0
            failed = 0
            recipients_seen = set()

            for recipient in configured_recipients:
                email = str(recipient.get("email") or "").strip().lower()
                if not email or email in recipients_seen:
                    continue
                recipients_seen.add(email)
                try:
                    subject, body = self.render(
                        digest_date=digest_date,
                        user_permissions={"dashboard.view", "dashboard.view_finance"},
                    )
                    self.mail.send(recipient=email, subject=subject, body=body, config=config)
                    delivery = EmailDigestDelivery(
                        digest_run_id=run.id,
                        user_id=0,
                        recipient_email=email,
                        status="SENT",
                        sent_at=utcnow(),
                    )
                    factory.session.add(delivery)
                    factory.session.commit()
                    delivered += 1
                except Exception as exc:
                    delivery = EmailDigestDelivery(
                        digest_run_id=run.id,
                        user_id=0,
                        recipient_email=email,
                        status="FAILED",
                        error_message=str(exc)[:2000],
                    )
                    factory.session.add(delivery)
                    factory.session.commit()
                    failed += 1

            for user in users:
                user_email = str(user.personal_email or "").strip().lower()
                if user_email in recipients_seen:
                    continue
                recipients_seen.add(user_email)
                existing = factory.session.query(EmailDigestDelivery).filter_by(digest_run_id=run.id, user_id=user.id).first()
                if existing is not None and existing.status == "SENT":
                    continue
                permissions = permissions_from_json(user.permissions_json, user.role)
                if "dashboard.view" not in permissions:
                    status = "SKIPPED-NO-DASHBOARD-ACCESS"
                    delivery = existing or EmailDigestDelivery(digest_run_id=run.id, user_id=user.id, recipient_email=user.personal_email, status=status)
                    delivery.recipient_email = user.personal_email
                    delivery.status = status
                    factory.session.add(delivery)
                    continue
                try:
                    subject, body = self.render(digest_date=digest_date, user_permissions=set(permissions))
                    self.mail.send(recipient=user.personal_email, subject=subject, body=body, config=config)
                    if existing is None:
                        existing = EmailDigestDelivery(digest_run_id=run.id, user_id=user.id, recipient_email=user.personal_email, status="SENT")
                    existing.recipient_email = user.personal_email
                    existing.status = "SENT"
                    existing.sent_at = utcnow()
                    existing.error_message = None
                    factory.session.add(existing)
                    delivered += 1
                except Exception as exc:
                    if existing is None:
                        existing = EmailDigestDelivery(digest_run_id=run.id, user_id=user.id, recipient_email=user.personal_email, status="FAILED")
                    existing.recipient_email = user.personal_email
                    existing.status = "FAILED"
                    existing.error_message = str(exc)[:2000]
                    factory.session.add(existing)
                    failed += 1
                factory.session.commit()

            if delivered == 0 and failed == 0:
                run.status = "FAILED-NO-RECIPIENT"
            else:
                run.status = "COMPLETED" if failed == 0 else "COMPLETED-WITH-ERRORS"
            run.completed_at = utcnow()
            factory.session.add(run)
            factory.session.commit()
            return {"status": run.status, "digest_date": digest_date.isoformat(), "run_id": run.id, "delivered": delivered, "failed": failed}
        finally:
            factory.close()

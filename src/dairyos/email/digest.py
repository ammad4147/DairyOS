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
from dairyos.api.milk_production_analytics import _yield_drop_watchlist
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)
from dairyos.farm.herd.services.animal_classification_service import (
    AnimalClassificationService,
    AnimalClassificationError,
)


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
                and classifier.is_active(x)
            ]
            revenue_received = sum(
                float(x.amount or 0)
                for x in records
                if (
                    str(getattr(x, "transaction_type", "") or "").upper() == "RECEIPT"
                    or (
                        classifier.is_income(x)
                        and str(getattr(x, "status", "") or "").upper() == "RECEIVED"
                    )
                )
            )
            expenses = sum(
                float(x.amount or 0)
                for x in records
                if classifier.is_expense(x)
            )
            return {
                "revenue_received": revenue_received,
                "expenses": expenses,
            }
        finally:
            factory.close()

    def _milk_snapshot(self, digest_date: date) -> dict:
        factory = RepositoryFactory.create()
        try:
            reconciliation = MilkReconciliationService(
                disposition_repository=factory.milk_dispositions(),
                production_repository=factory.milk(),
            ).reconcile(digest_date, raise_finding=False)

            dispositions = [
                item for item in factory.milk_dispositions().get_by_date(digest_date)
                if str(getattr(item, "status", "RECORDED") or "RECORDED").upper() != "VOID"
            ]
            by_type = {}
            for item in dispositions:
                key = str(getattr(item, "disposition_type", "") or "").upper()
                by_type[key] = by_type.get(key, 0.0) + float(
                    getattr(item, "quantity_litres", 0.0) or 0.0
                )

            service = MilkProductionTrendIntelligenceService(repository_factory=factory)
            animals = service._eligible_animals(factory)
            histories = service._animal_histories(factory, animals)
            records = factory.milk().get_all()
            watchlist = _yield_drop_watchlist(
                service=service,
                records=records,
                animals=animals,
                histories=histories,
                target_date=digest_date,
                lookback_days=30,
            )

            trend = service.generate(
                as_of_date=digest_date,
                period_days=7,
            ).summary()
            change = trend.get("variance_percentage")
            if change is None:
                change = trend.get("change_percent")

            return {
                "total_yield": reconciliation.get("biological_production_litres"),
                "change_percent": change,
                "sold": by_type.get("SOLD", 0.0),
                "domestic_use": by_type.get("DOMESTIC_USE", 0.0),
                "calf_feed": by_type.get("CALF_FEED", 0.0),
                "wastage": by_type.get("WASTAGE", 0.0),
                "other": by_type.get("OTHER", 0.0),
                "unaccounted": reconciliation.get("unaccounted_saleable_litres", 0.0) or 0.0,
                "watchlist": watchlist,
            }
        finally:
            factory.close()

    def _herd_snapshot(self, digest_date: date) -> dict:
        factory = RepositoryFactory.create()
        try:
            animals = list(factory.animal().active_animals() or [])
            counts = {
                "Milking": 0,
                "Dry": 0,
                "Heifer": 0,
                "Female Calf": 0,
                "Male Calf": 0,
                "Bull": 0,
            }
            for animal in animals:
                try:
                    category = AnimalClassificationService.classify(
                        getattr(animal, "lifecycle_status", None),
                        getattr(animal, "sex", None),
                    ).category.value
                except AnimalClassificationError:
                    continue
                if category in counts:
                    counts[category] += 1

            mortalities = []
            for event in self.container.event_journal.all_events():
                if getattr(event, "name", None) != "OperationalInputReceived":
                    continue
                payload = dict(getattr(event, "payload", {}) or {})
                if str(payload.get("input_type") or "").lower() != "animal_disposition":
                    continue
                if str(payload.get("disposition") or "").upper() != "DECEASED":
                    continue
                if str(payload.get("effective_date") or "")[:10] != digest_date.isoformat():
                    continue
                animal_id = str(payload.get("animal_id") or "")
                animal = factory.animal().get_by_animal_id(animal_id)
                mortalities.append(
                    {
                        "animal_id": animal_id,
                        "category": (
                            AnimalClassificationService.classify(
                                getattr(animal, "lifecycle_status", None),
                                getattr(animal, "sex", None),
                            ).category.value
                            if animal is not None else "Unknown"
                        ),
                        "breed": getattr(animal, "breed", None) if animal is not None else None,
                        "cause": payload.get("cause") or payload.get("reason"),
                    }
                )

            return {"total": len(animals), "counts": counts, "mortalities": mortalities}
        finally:
            factory.close()

    def _active_warnings(self) -> list[str]:
        factory = RepositoryFactory.create()
        try:
            findings = factory.operational_findings().get_open()
            return [
                str(getattr(item, "title", None) or getattr(item, "detail", None) or "Operational warning")
                for item in findings
            ]
        finally:
            factory.close()


    def render(self, *, digest_date: date, user_permissions: set[str]) -> tuple[str, str]:
        dashboard = self._dashboard()
        health = dashboard.get("health", {})
        milk = self._milk_snapshot(digest_date)
        herd = self._herd_snapshot(digest_date)
        warnings = self._active_warnings()

        subject = f"DairyOS Daily Summary — {digest_date.isoformat()}"
        lines = [
            subject,
            f"Operational Date: {digest_date.isoformat()}",
            "",
            "MILK PRODUCTION",
            f"Total yield today: {float(milk['total_yield'] or 0.0):.1f} litres",
        ]

        change = milk.get("change_percent")
        lines.append(
            "Change vs previous recorded day: "
            + (f"{float(change):+.1f}%" if change is not None else "N/A")
        )
        lines += [
            "",
            "Milk Disposition",
            f"Milk Sold: {float(milk['sold']):.1f} litres",
            f"Domestic Use: {float(milk['domestic_use']):.1f} litres",
            f"Calves Feed: {float(milk['calf_feed']):.1f} litres",
            f"Wastage: {float(milk['wastage']):.1f} litres",
        ]
        if float(milk.get("other") or 0.0) > 0:
            lines.append(f"Other Governed Disposition: {float(milk['other']):.1f} litres")
        lines.append(f"Unaccounted Milk: {float(milk['unaccounted']):.1f} litres")

        lines += ["", "YIELD DROP WATCHLIST"]
        watchlist = milk.get("watchlist") or []
        if not watchlist:
            lines.append("No animals on the Yield Drop Watchlist.")
        else:
            for item in watchlist:
                lines.append(
                    f"- {item.get('animal_id')}: "
                    f"{float(item.get('previous_litres') or 0.0):.1f} L → "
                    f"{float(item.get('current_litres') or 0.0):.1f} L; "
                    f"drop {float(item.get('drop_percentage') or 0.0):.1f}%; "
                    f"severity {item.get('severity') or 'N/A'}"
                )

        counts = herd["counts"]
        lines += [
            "",
            "HERD STATUS",
            f"Total headcount: {herd['total']}",
            f"Milking: {counts['Milking']}",
            f"Dry: {counts['Dry']}",
            f"Heifers: {counts['Heifer']}",
            f"Female Calves: {counts['Female Calf']}",
            f"Male Calves: {counts['Male Calf']}",
            f"Bulls: {counts['Bull']}",
            "",
            f"Active health Alerts: {health.get('active_exceptions', 0)}",
        ]

        mortalities = herd.get("mortalities") or []
        lines.append(f"Any Mortalities? {'Yes' if mortalities else 'No'}")
        for mortality in mortalities:
            basic = " · ".join(
                part for part in [
                    mortality.get("category"),
                    mortality.get("breed"),
                ] if part
            )
            detail = f"- Animal ID: {mortality.get('animal_id')} · {basic or 'Basic information unavailable'}"
            if mortality.get("cause"):
                detail += f" · Cause/Reason: {mortality['cause']}"
            lines.append(detail)

        if "finance.view" in user_permissions or "dashboard.view_finance" in user_permissions:
            finance = self._financial_snapshot(digest_date)
            lines += [
                "",
                "FINANCIAL SNAPSHOT",
                f"Revenue Received today: {_money(finance['revenue_received'])}",
                f"Expenses today: {_money(finance['expenses'])}",
            ]

        lines += ["", "ACTIVE WARNINGS"]
        if not warnings:
            lines.append("No active operational warnings.")
        else:
            for warning in warnings[:10]:
                lines.append(f"- {warning}")

        lines += [
            "",
            "This digest reflects governed DairyOS records for the operational date shown. "
            "Active warnings reflect unresolved findings at generation time.",
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
                existing_delivery = (
                    factory.session.query(EmailDigestDelivery)
                    .filter(
                        EmailDigestDelivery.digest_run_id == run.id,
                        EmailDigestDelivery.user_id.is_(None),
                        EmailDigestDelivery.recipient_email == email,
                    )
                    .first()
                )
                if existing_delivery is not None and existing_delivery.status == "SENT":
                    continue
                try:
                    subject, body = self.render(
                        digest_date=digest_date,
                        user_permissions={"dashboard.view", "dashboard.view_finance"},
                    )
                    self.mail.send(recipient=email, subject=subject, body=body, config=config)
                    delivery = existing_delivery or EmailDigestDelivery(
                        digest_run_id=run.id,
                        user_id=None,
                        recipient_email=email,
                        status="SENT",
                    )
                    delivery.status = "SENT"
                    delivery.sent_at = utcnow()
                    delivery.error_message = None
                    factory.session.add(delivery)
                    factory.session.commit()
                    delivered += 1
                except Exception as exc:
                    delivery = existing_delivery or EmailDigestDelivery(
                        digest_run_id=run.id,
                        user_id=None,
                        recipient_email=email,
                        status="FAILED",
                    )
                    delivery.status = "FAILED"
                    delivery.error_message = str(exc)[:2000]
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

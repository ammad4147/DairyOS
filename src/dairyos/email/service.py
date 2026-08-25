from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from dairyos.core.time_utils import utcnow
from dairyos.data.models.email_sender_setting import EmailSenderSetting
from dairyos.data.repositories.repository_factory import RepositoryFactory
from .crypto import decrypt_secret, encrypt_secret


@dataclass(frozen=True)
class EmailSenderConfig:
    sender_email: str
    sender_display_name: str | None
    smtp_host: str
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    use_tls: bool


class EmailService:
    """Resolve sender configuration from DB-overrides or deployment defaults."""

    def get_config(self) -> EmailSenderConfig | None:
        factory = RepositoryFactory.create()
        try:
            row = factory.session.query(EmailSenderSetting).filter(EmailSenderSetting.id == 1).first()
            if row is not None:
                host = row.smtp_host or ""
                if not row.sender_email or not host:
                    return None
                return EmailSenderConfig(
                    sender_email=row.sender_email,
                    sender_display_name=row.sender_display_name,
                    smtp_host=host,
                    smtp_port=int(row.smtp_port or 587),
                    smtp_username=row.smtp_username,
                    smtp_password=decrypt_secret(row.smtp_password_ciphertext),
                    use_tls=bool(row.use_tls),
                )
        finally:
            factory.close()

        sender_email = os.getenv("DAIRYOS_EMAIL_SENDER", "").strip()
        smtp_host = os.getenv("DAIRYOS_SMTP_HOST", "").strip()
        if not sender_email or not smtp_host:
            return None
        return EmailSenderConfig(
            sender_email=sender_email,
            sender_display_name=os.getenv("DAIRYOS_EMAIL_SENDER_NAME", "DairyOS").strip() or None,
            smtp_host=smtp_host,
            smtp_port=int(os.getenv("DAIRYOS_SMTP_PORT", "587")),
            smtp_username=os.getenv("DAIRYOS_SMTP_USERNAME") or None,
            smtp_password=os.getenv("DAIRYOS_SMTP_PASSWORD") or None,
            use_tls=os.getenv("DAIRYOS_SMTP_TLS", "true").strip().lower() in {"1", "true", "yes", "on"},
        )

    def save_config(self, payload: dict, updated_by: str) -> dict:
        factory = RepositoryFactory.create()
        try:
            row = factory.session.query(EmailSenderSetting).filter(EmailSenderSetting.id == 1).first()
            if row is None:
                row = EmailSenderSetting(id=1, sender_email=str(payload["sender_email"]).strip())
                factory.session.add(row)
            row.sender_email = str(payload["sender_email"]).strip()
            row.sender_display_name = str(payload.get("sender_display_name") or "").strip() or None
            row.smtp_host = str(payload["smtp_host"]).strip()
            row.smtp_port = int(payload.get("smtp_port") or 587)
            row.smtp_username = str(payload.get("smtp_username") or "").strip() or None
            row.use_tls = bool(payload.get("use_tls", True))
            if payload.get("smtp_password"):
                row.smtp_password_ciphertext = encrypt_secret(str(payload["smtp_password"]))
            row.updated_by = updated_by
            row.updated_at = utcnow()
            factory.session.commit()
            return self.public_config()
        finally:
            factory.close()

    def public_config(self) -> dict:
        factory = RepositoryFactory.create()
        try:
            row = factory.session.query(EmailSenderSetting).filter(EmailSenderSetting.id == 1).first()
            if row is None:
                cfg = self.get_config()
                if cfg is None:
                    return {"configured": False}
                return {
                    "configured": True,
                    "source": "config",
                    "sender_email": cfg.sender_email,
                    "sender_display_name": cfg.sender_display_name,
                    "smtp_host": cfg.smtp_host,
                    "smtp_port": cfg.smtp_port,
                    "smtp_username": cfg.smtp_username,
                    "use_tls": cfg.use_tls,
                    "password_configured": bool(cfg.smtp_password),
                }
            return {
                "configured": bool(row.sender_email and row.smtp_host),
                "source": "database",
                "sender_email": row.sender_email,
                "sender_display_name": row.sender_display_name,
                "smtp_host": row.smtp_host,
                "smtp_port": row.smtp_port,
                "smtp_username": row.smtp_username,
                "use_tls": row.use_tls,
                "password_configured": bool(row.smtp_password_ciphertext),
            }
        finally:
            factory.close()

    def send(self, *, recipient: str, subject: str, body: str, config: EmailSenderConfig | None = None) -> None:
        cfg = config or self.get_config()
        if cfg is None:
            raise RuntimeError("DairyOS email sender is not configured")
        msg = EmailMessage()
        msg["From"] = f"{cfg.sender_display_name} <{cfg.sender_email}>" if cfg.sender_display_name else cfg.sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as smtp:
            if cfg.use_tls:
                smtp.starttls()
            if cfg.smtp_username:
                smtp.login(cfg.smtp_username, cfg.smtp_password or "")
            smtp.send_message(msg)

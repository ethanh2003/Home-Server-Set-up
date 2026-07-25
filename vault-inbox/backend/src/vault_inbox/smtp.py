from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .config import Settings


def send_alert(settings: Settings, *, subject: str, body: str) -> dict[str, object]:
    if not settings.smtp_enabled:
        return {"ok": False, "skipped": True, "message": "SMTP disabled"}
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = settings.smtp_to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.send_message(message)
    return {"ok": True, "to": settings.smtp_to}

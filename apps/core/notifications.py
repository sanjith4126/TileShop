"""
Optional email alerts to the shop (new quote requests and orders).

Nothing is sent unless SHOP_NOTIFICATION_EMAIL and an email server are
configured. Failures are logged and never break the customer's request.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


def shop_email_configured():
    if not settings.SHOP_NOTIFICATION_EMAIL:
        return False
    # The SMTP backend needs a server; other backends (console, locmem in tests) don't.
    return bool(settings.EMAIL_HOST) or settings.EMAIL_BACKEND != SMTP_BACKEND


def notify_shop(subject, body):
    """Email the shop. Returns True if the message was handed to the mail server."""
    if not shop_email_configured():
        return False
    subject = " ".join(f"[{settings.SITE_NAME}] {subject}".split())
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.SHOP_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Could not send shop notification email: %s", subject)
        return False
    return True

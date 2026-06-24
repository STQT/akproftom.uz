"""Show Telegram getWebhookInfo and whether this process sees the secret.

    python manage.py webhook_info

Useful to debug 403s: a 403 means the secret Telegram sends doesn't match
TELEGRAM_WEBHOOK_SECRET as seen by the running app.
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from core import telegram as tg


class Command(BaseCommand):
    help = "Print Telegram webhook info and the locally-configured secret length."

    def handle(self, *args, **options):
        secret = (settings.TELEGRAM_WEBHOOK_SECRET or "").strip()
        base = (settings.TELEGRAM_WEBHOOK_BASE or "").strip().rstrip("/")
        self.stdout.write("Local config (as this process sees it):")
        self.stdout.write(f"  TELEGRAM_WEBHOOK_BASE   : {base or '(empty)'}")
        self.stdout.write(f"  TELEGRAM_WEBHOOK_SECRET : "
                          f"{'set, len=%d' % len(secret) if secret else '(EMPTY!)'}")
        self.stdout.write(f"  expected webhook URL    : {base + '/telegram/webhook/' if base else '(unknown)'}")

        info = tg.api_call("getWebhookInfo")
        self.stdout.write("\ngetWebhookInfo:")
        if info is None:
            self.stderr.write("  request failed — check TELEGRAM_BOT_TOKEN/logs.")
            return
        for key in ("url", "pending_update_count", "last_error_date",
                    "last_error_message", "ip_address",
                    "has_custom_certificate", "max_connections"):
            if key in info:
                self.stdout.write(f"  {key}: {info[key]}")

"""Register the Telegram webhook and bot commands (requires HTTPS).

    python manage.py set_webhook

Reads TELEGRAM_WEBHOOK_BASE (e.g. https://akproftom.uz) and
TELEGRAM_WEBHOOK_SECRET from settings/env. Telegram only accepts HTTPS
webhook URLs, so this works only once SSL is live.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core import telegram as tg


class Command(BaseCommand):
    help = "Register the Telegram webhook + bot commands (private chats only)."

    def handle(self, *args, **options):
        if not (settings.TELEGRAM_BOT_TOKEN or "").strip():
            raise CommandError("TELEGRAM_BOT_TOKEN is not set.")
        base = (settings.TELEGRAM_WEBHOOK_BASE or "").strip().rstrip("/")
        if not base.startswith("https://"):
            raise CommandError(
                "TELEGRAM_WEBHOOK_BASE must be an https:// URL (Telegram requires "
                "HTTPS). Set it after SSL is installed.")
        secret = (settings.TELEGRAM_WEBHOOK_SECRET or "").strip()
        if not secret:
            raise CommandError("TELEGRAM_WEBHOOK_SECRET is not set.")

        url = f"{base}/telegram/webhook/"
        result = tg.api_call(
            "setWebhook",
            url=url,
            secret_token=secret,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        if result is None:
            raise CommandError("setWebhook failed — check logs/token.")

        # Commands shown in the private-chat menu only.
        tg.api_call(
            "setMyCommands",
            commands=[
                {"command": "start", "description": "Меню"},
                {"command": "catalog", "description": "Каталог"},
            ],
            scope={"type": "all_private_chats"},
        )
        self.stdout.write(self.style.SUCCESS(f"Webhook set: {url}"))

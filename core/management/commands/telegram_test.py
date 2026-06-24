"""Send a test message to the configured Telegram chat(s).

    python manage.py telegram_test
    python manage.py telegram_test --text "Привет из akproftom.uz"

Useful to verify TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID on the server.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.telegram import send_message


class Command(BaseCommand):
    help = "Send a test Telegram message to verify bot configuration."

    def add_arguments(self, parser):
        parser.add_argument("--text", default="✅ Тест уведомлений akproftom.uz")

    def handle(self, *args, **options):
        if not (settings.TELEGRAM_BOT_TOKEN or "").strip():
            raise CommandError("TELEGRAM_BOT_TOKEN is not set.")
        if not (settings.TELEGRAM_CHAT_ID or "").strip():
            raise CommandError("TELEGRAM_CHAT_ID is not set.")
        # Blocking so errors surface in the console instead of a daemon thread.
        send_message(options["text"], blocking=True)
        self.stdout.write(self.style.SUCCESS(
            f"Sent to chat_id(s): {settings.TELEGRAM_CHAT_ID}"))

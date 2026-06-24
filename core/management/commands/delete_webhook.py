"""Remove the Telegram webhook.

    python manage.py delete_webhook
"""

from django.core.management.base import BaseCommand

from core import telegram as tg


class Command(BaseCommand):
    help = "Delete the Telegram webhook."

    def handle(self, *args, **options):
        result = tg.api_call("deleteWebhook", drop_pending_updates=False)
        if result is None:
            self.stderr.write("deleteWebhook failed — check token/logs.")
        else:
            self.stdout.write(self.style.SUCCESS("Webhook deleted."))

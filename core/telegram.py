"""Telegram notifications for site inquiries.

Sends a message to one or more chat IDs via the Bot API. Uses only the
standard library (urllib) — no extra dependencies. Sending happens in a
daemon thread and never raises into the request: a Telegram outage must not
break the «заявка» form.

Configure via env (see .env.example):
    TELEGRAM_BOT_TOKEN=123456:ABC-...
    TELEGRAM_CHAT_ID=-1001234567890         # one id, or comma-separated for several
"""

import json
import logging
import threading
import urllib.request

from django.conf import settings
from django.utils.html import escape

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _chat_ids():
    raw = (settings.TELEGRAM_CHAT_ID or "").strip()
    return [c.strip() for c in raw.split(",") if c.strip()]


def _post(token, chat_id, text):
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL.format(token=token),
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def _send(text):
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    chats = _chat_ids()
    if not token or not chats:
        logger.warning("Telegram not configured (token/chat_id missing); skipping")
        return
    for chat_id in chats:
        try:
            _post(token, chat_id, text)
        except Exception:
            logger.exception("Telegram send failed for chat_id=%s", chat_id)


def send_message(text, *, blocking=False):
    """Send `text` to the configured chat(s). Fire-and-forget by default."""
    if blocking:
        _send(text)
    else:
        threading.Thread(target=_send, args=(text,), daemon=True).start()


def notify_inquiry(inquiry):
    """Format and send a notification for a saved Inquiry."""
    lines = [
        "🆕 <b>Новая заявка с сайта</b>",
        f"👤 <b>Имя:</b> {escape(inquiry.name)}",
        f"📞 <b>Телефон:</b> {escape(inquiry.phone)}",
    ]
    if inquiry.product_id and inquiry.product:
        lines.append(f"📦 <b>Товар:</b> {escape(inquiry.product.name)}")
    if inquiry.message:
        lines.append(f"💬 <b>Сообщение:</b>\n{escape(inquiry.message)}")
    if inquiry.source_url:
        lines.append(f"🔗 {escape(inquiry.source_url)}")
    send_message("\n".join(lines))

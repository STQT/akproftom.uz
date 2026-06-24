"""Telegram Bot API helpers and site-inquiry notifications.

Uses only the standard library (urllib) — no extra dependencies. Outbound
notifications are sent in a daemon thread and never raise into the request:
a Telegram outage must not break the «заявка» form.

Configure via env (see .env.example):
    TELEGRAM_BOT_TOKEN=123456:ABC-...
    TELEGRAM_CHAT_ID=-1001234567890         # one id, or comma-separated for several
"""

import json
import logging
import threading
import urllib.error
import urllib.request

from django.conf import settings
from django.utils.html import escape

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _token():
    return (settings.TELEGRAM_BOT_TOKEN or "").strip()


def api_call(method, _timeout=30, **params):
    """Call a Bot API `method` with JSON `params`.

    Returns the parsed `result` on success, or None on any error (logged).
    `_timeout` is the socket timeout; Telegram's own long-poll `timeout`
    param is passed through **params for getUpdates.
    """
    token = _token()
    if not token:
        logger.warning("Telegram token missing; cannot call %s", method)
        return None
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        API_BASE.format(token=token, method=method),
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        logger.error("Telegram %s HTTP %s: %s", method, e.code, body)
        return None
    except Exception:
        logger.exception("Telegram %s request failed", method)
        return None
    if not payload.get("ok"):
        logger.error("Telegram %s returned error: %s", method, payload)
        return None
    return payload.get("result")


# --- Outbound notifications to the admin chat(s) ---------------------------

def _chat_ids():
    raw = (settings.TELEGRAM_CHAT_ID or "").strip()
    return [c.strip() for c in raw.split(",") if c.strip()]


def _send(text):
    if not _token() or not _chat_ids():
        logger.warning("Telegram not configured (token/chat_id missing); skipping")
        return
    for chat_id in _chat_ids():
        api_call("sendMessage", chat_id=chat_id, text=text,
                 parse_mode="HTML", disable_web_page_preview=True)


def send_message(text, *, blocking=False):
    """Send `text` to the configured admin chat(s). Fire-and-forget by default."""
    if blocking:
        _send(text)
    else:
        threading.Thread(target=_send, args=(text,), daemon=True).start()


def notify_inquiry(inquiry, *, via_bot=False):
    """Format and send a notification for a saved Inquiry to the admin chat(s)."""
    lines = [
        "🆕 <b>Новая заявка%s</b>" % (" (из бота)" if via_bot else " с сайта"),
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

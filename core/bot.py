"""Telegram bot logic: catalog browsing + inquiry flow.

Transport-agnostic — `handle_update(update)` is fed by the webhook view (and
could be fed by a poller too). The bot operates in PRIVATE CHATS ONLY; any
update from a group/supergroup/channel is ignored.

Conversation state for the multi-step inquiry lives in the BotDialog model,
so it survives across Passenger worker processes.
"""

import logging

from django.conf import settings
from django.utils.html import escape

from catalog.models import Category, Product

from . import telegram as tg
from .models import BotDialog, Inquiry

logger = logging.getLogger(__name__)

COMPANY = "TASHKENT PROFNASTIL SERVIS"


# --- helpers ---------------------------------------------------------------

def _full_name(user):
    parts = [user.get("first_name", ""), user.get("last_name", "")]
    return " ".join(p for p in parts if p).strip()


def _webapp_url():
    # Tolerate accidental inline comments / trailing spaces in the env value
    # (django-environ keeps everything after `=`), so a messy value just hides
    # the button instead of breaking the whole message with a 400.
    raw = (getattr(settings, "TELEGRAM_WEBAPP_URL", "") or "")
    raw = raw.split("#", 1)[0].strip()
    raw = raw.split()[0] if raw else ""
    return raw if raw.startswith("https://") else ""  # web_app requires https


def _main_menu_kb():
    rows = [[{"text": "🗂 Каталог", "callback_data": "home"}]]
    url = _webapp_url()
    if url:
        rows.append([{"text": "🌐 Открыть сайт", "web_app": {"url": url}}])
    rows.append([{"text": "📝 Оставить заявку", "callback_data": "inq:0"}])
    return {"inline_keyboard": rows}


def _root_kb():
    cats = Category.objects.filter(is_active=True, parent__isnull=True).order_by("order", "name")
    rows = [[{"text": c.name, "callback_data": f"cat:{c.id}"}] for c in cats]
    rows.append([{"text": "📝 Оставить заявку", "callback_data": "inq:0"}])
    rows.append([{"text": "⬅ В меню", "callback_data": "menu"}])
    return {"inline_keyboard": rows}


def _edit_or_send(chat_id, message_id, has_photo, text, kb):
    """Update the current message in place, or (if it's a photo card that
    can't be edited into text) delete it and send a fresh text message."""
    if has_photo:
        tg.api_call("deleteMessage", chat_id=chat_id, message_id=message_id)
        tg.api_call("sendMessage", chat_id=chat_id, text=text,
                    parse_mode="HTML", reply_markup=kb)
    else:
        tg.api_call("editMessageText", chat_id=chat_id, message_id=message_id,
                    text=text, parse_mode="HTML", reply_markup=kb)


# --- screens ---------------------------------------------------------------

def _menu_text(user=None):
    name = _full_name(user) if user else ""
    hi = f", {escape(name)}" if name else ""
    return (
        f"Здравствуйте{hi}! 👋\n\n"
        f"<b>{COMPANY}</b>\n"
        "Сэндвич-панели, профнастил, металлоконструкции и прокат.\n\n"
        "Выберите действие:"
    )


def _send_welcome(chat_id, user):
    tg.api_call("sendMessage", chat_id=chat_id, text=_menu_text(user),
                parse_mode="HTML", reply_markup=_main_menu_kb())


def _show_menu(chat_id, message_id, has_photo):
    _edit_or_send(chat_id, message_id, has_photo, _menu_text(), _main_menu_kb())


def _show_root(chat_id, message_id=None, has_photo=False):
    text = "🗂 <b>Каталог</b>\nВыберите категорию:"
    if message_id is None:
        tg.api_call("sendMessage", chat_id=chat_id, text=text,
                    parse_mode="HTML", reply_markup=_root_kb())
    else:
        _edit_or_send(chat_id, message_id, has_photo, text, _root_kb())


def _show_category(chat_id, message_id, has_photo, cat_id):
    cat = Category.objects.filter(id=cat_id, is_active=True).first()
    if not cat:
        return _show_root(chat_id, message_id, has_photo)
    back = f"cat:{cat.parent_id}" if cat.parent_id else "home"
    children = list(cat.children.filter(is_active=True).order_by("order", "name"))
    if children:
        rows = [[{"text": c.name, "callback_data": f"cat:{c.id}"}] for c in children]
        text = f"<b>{escape(cat.name)}</b>\nВыберите подкатегорию:"
    else:
        products = list(cat.products.filter(is_active=True).order_by("order", "name"))
        rows = [[{"text": p.name, "callback_data": f"prod:{p.id}"}] for p in products]
        text = f"<b>{escape(cat.name)}</b>"
        if not products:
            text += "\nПока нет товаров в этой категории."
    rows.append([{"text": "⬅ Назад", "callback_data": back}])
    _edit_or_send(chat_id, message_id, has_photo, text, {"inline_keyboard": rows})


def _show_product(chat_id, prod_id):
    p = (Product.objects.filter(id=prod_id, is_active=True)
         .select_related("category").prefetch_related("specs").first())
    if not p:
        return
    lines = [f"<b>{escape(p.name)}</b>"]
    if p.short_description:
        lines.append(escape(p.short_description))
    specs = list(p.specs.all())[:15]
    if specs:
        lines.append("")
        lines += [f"• {escape(s.name)}: {escape(s.value)}" for s in specs]
    caption = "\n".join(lines)[:1024]
    kb = {"inline_keyboard": [
        [{"text": "📝 Оставить заявку", "callback_data": f"inq:{p.id}"}],
        [{"text": "⬅ К категории", "callback_data": f"cat:{p.category_id}"}],
    ]}
    photo = None
    try:
        if p.main_image:
            photo = p.main_image.url
    except Exception:
        photo = None
    if photo:
        tg.api_call("sendPhoto", chat_id=chat_id, photo=photo, caption=caption,
                    parse_mode="HTML", reply_markup=kb)
    else:
        tg.api_call("sendMessage", chat_id=chat_id, text=caption,
                    parse_mode="HTML", reply_markup=kb)


# --- inquiry flow ----------------------------------------------------------

def _start_inquiry(chat_id, product_id, user):
    product = Product.objects.filter(id=product_id).first() if product_id else None
    BotDialog.objects.update_or_create(
        chat_id=chat_id,
        defaults={"step": "phone", "name": _full_name(user),
                  "phone": "", "product": product},
    )
    kb = {
        "keyboard": [[{"text": "📞 Отправить мой номер", "request_contact": True}]],
        "resize_keyboard": True, "one_time_keyboard": True,
    }
    intro = f"Заявка по товару «{product.name}».\n" if product else ""
    tg.api_call("sendMessage", chat_id=chat_id,
                text=f"{intro}Отправьте номер телефона — кнопкой ниже или введите вручную.",
                reply_markup=kb)


def _continue_inquiry(chat_id, msg, dialog):
    if dialog.step == "phone":
        contact = msg.get("contact") or {}
        phone = contact.get("phone_number") or (msg.get("text") or "").strip()
        if not phone or phone.startswith("/"):
            tg.api_call("sendMessage", chat_id=chat_id,
                        text="Не вижу номер. Отправьте телефон кнопкой или текстом.")
            return
        dialog.phone = phone[:40]
        dialog.step = "message"
        dialog.save(update_fields=["phone", "step", "updated_at"])
        tg.api_call("sendMessage", chat_id=chat_id,
                    text="Добавьте комментарий к заявке или отправьте /skip.",
                    reply_markup={"remove_keyboard": True})
    elif dialog.step == "message":
        text = (msg.get("text") or "").strip()
        message = "" if text in ("/skip", "-") else text
        _save_inquiry(chat_id, dialog, message)


def _save_inquiry(chat_id, dialog, message):
    inquiry = Inquiry.objects.create(
        name=dialog.name or "Telegram",
        phone=dialog.phone,
        message=message,
        product=dialog.product,
        source_url="Telegram-бот",
    )
    dialog.delete()
    tg.notify_inquiry(inquiry, via_bot=True)
    tg.api_call("sendMessage", chat_id=chat_id,
                text="✅ Спасибо! Заявка принята — мы свяжемся с вами.",
                reply_markup=_main_menu_kb())


# --- dispatch --------------------------------------------------------------

def _is_private(chat):
    return bool(chat) and chat.get("type") == "private"


def handle_update(update):
    """Entry point for a single Telegram update (from the webhook)."""
    try:
        if "message" in update:
            _handle_message(update["message"])
        elif "callback_query" in update:
            _handle_callback(update["callback_query"])
    except Exception:
        logger.exception("Bot failed on update %s", update.get("update_id"))


def _handle_message(msg):
    chat = msg.get("chat", {})
    if not _is_private(chat):
        return  # groups/channels are ignored entirely
    chat_id = chat["id"]
    text = (msg.get("text") or "").strip()

    if text in ("/start", "/menu"):
        BotDialog.objects.filter(chat_id=chat_id).delete()
        _send_welcome(chat_id, msg.get("from", {}))
        return
    if text == "/catalog":
        BotDialog.objects.filter(chat_id=chat_id).delete()
        _show_root(chat_id)
        return

    dialog = BotDialog.objects.filter(chat_id=chat_id).first()
    if dialog:
        _continue_inquiry(chat_id, msg, dialog)
        return

    _send_welcome(chat_id, msg.get("from", {}))


def _handle_callback(cq):
    msg = cq.get("message", {})
    chat = msg.get("chat", {})
    cq_id = cq.get("id")
    if not _is_private(chat):
        tg.api_call("answerCallbackQuery", callback_query_id=cq_id)
        return
    chat_id = chat["id"]
    message_id = msg.get("message_id")
    has_photo = bool(msg.get("photo"))
    data = cq.get("data", "")
    tg.api_call("answerCallbackQuery", callback_query_id=cq_id)

    try:
        if data == "menu":
            _show_menu(chat_id, message_id, has_photo)
        elif data == "home":
            _show_root(chat_id, message_id, has_photo)
        elif data.startswith("cat:"):
            _show_category(chat_id, message_id, has_photo, int(data[4:]))
        elif data.startswith("prod:"):
            _show_product(chat_id, int(data[5:]))
        elif data.startswith("inq:"):
            _start_inquiry(chat_id, int(data[4:]), cq.get("from", {}))
    except (ValueError, IndexError):
        logger.warning("Bad callback data: %r", data)

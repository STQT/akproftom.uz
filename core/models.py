from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    """Singleton holding global, editable site content (contacts, about texts)."""

    company_name = models.CharField(_("Название компании"), max_length=200,
                                    default="TASHKENT PROFNASTIL SERVIS")
    address = models.CharField(_("Адрес"), max_length=300, blank=True)
    work_hours = models.CharField(_("Часы работы"), max_length=150, blank=True)
    email = models.EmailField(_("E-mail"), blank=True)
    map_embed = models.TextField(
        _("Карта (iframe / embed)"), blank=True,
        help_text=_("HTML-код встраиваемой карты (Яндекс/Google)."),
    )
    instagram = models.URLField(_("Instagram (Профнастил)"), blank=True)
    instagram2 = models.URLField(_("Instagram (Сэндвич-панель)"), blank=True)
    telegram = models.URLField(_("Telegram"), blank=True)
    about_text = models.TextField(_("О компании"), blank=True)
    process_text = models.TextField(_("Технологический процесс"), blank=True)

    class Meta:
        verbose_name = _("Настройки сайта")
        verbose_name_plural = _("Настройки сайта")

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # never delete the singleton

    @classmethod
    def get(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class Phone(models.Model):
    """A contact number, optionally labelled by direction (Сэндвич-панели и т.д.)."""

    number = models.CharField(_("Номер"), max_length=40)
    label = models.CharField(_("Направление / подпись"), max_length=120, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Телефон")
        verbose_name_plural = _("Телефоны")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.label}: {self.number}" if self.label else self.number

    @property
    def tel_href(self):
        """Strip spaces/dashes for a usable tel: link."""
        return "tel:" + "".join(c for c in self.number if c.isdigit() or c == "+")


class Certificate(models.Model):
    title = models.CharField(_("Название"), max_length=200, blank=True)
    image = models.ImageField(_("Изображение"), upload_to="certificates/")
    file = models.FileField(_("Файл (PDF)"), upload_to="certificates/files/", blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Сертификат")
        verbose_name_plural = _("Сертификаты")
        ordering = ["order", "id"]

    def __str__(self):
        return self.title or f"Сертификат #{self.pk}"


class Inquiry(models.Model):
    """A lead submitted via a «заявка на расчёт» form."""

    name = models.CharField(_("Имя"), max_length=150)
    phone = models.CharField(_("Телефон"), max_length=40)
    message = models.TextField(_("Сообщение"), blank=True)
    product = models.ForeignKey(
        "catalog.Product", verbose_name=_("Товар"), on_delete=models.SET_NULL,
        null=True, blank=True, related_name="inquiries",
    )
    source_url = models.CharField(_("Страница"), max_length=300, blank=True)
    is_processed = models.BooleanField(_("Обработана"), default=False)
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True)

    class Meta:
        verbose_name = _("Заявка")
        verbose_name_plural = _("Заявки")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class BotDialog(models.Model):
    """Per-user conversation state for the Telegram bot's inquiry flow.

    Persisted in the DB (not memory) because the webhook runs under Passenger
    where several worker processes may handle consecutive updates.
    """

    chat_id = models.BigIntegerField(_("Chat ID"), unique=True)
    step = models.CharField(_("Шаг"), max_length=20, blank=True)
    name = models.CharField(_("Имя"), max_length=150, blank=True)
    phone = models.CharField(_("Телефон"), max_length=40, blank=True)
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.SET_NULL, null=True, blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Диалог бота")
        verbose_name_plural = _("Диалоги бота")

    def __str__(self):
        return f"{self.chat_id} @ {self.step or '-'}"

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from catalog.models import unique_slug


class ServiceGroup(models.Model):
    """A heading that groups related services (e.g. «Механическая обработка»)."""

    title = models.CharField(_("Название"), max_length=150)
    slug = models.SlugField(_("Слаг"), max_length=170, unique=True, blank=True)
    description = models.CharField(_("Подзаголовок"), max_length=300, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Группа услуг")
        verbose_name_plural = _("Группы услуг")
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(ServiceGroup, self.title)
        super().save(*args, **kwargs)


class Service(models.Model):
    """A single service offered (e.g. «Токарная обработка»)."""

    group = models.ForeignKey(
        ServiceGroup,
        verbose_name=_("Группа"),
        on_delete=models.SET_NULL,
        related_name="services",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Название"), max_length=200)
    slug = models.SlugField(_("Слаг"), max_length=220, unique=True, blank=True)
    short_description = models.CharField(_("Краткое описание"), max_length=300, blank=True)
    description = models.TextField(_("Описание"), blank=True)
    image = models.ImageField(_("Изображение"), upload_to="services/", blank=True)
    is_featured = models.BooleanField(_("Показывать на главной"), default=False)
    is_active = models.BooleanField(_("Активна"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Услуга")
        verbose_name_plural = _("Услуги")
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Service, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("services:detail", args=[self.slug])


class ServiceImage(models.Model):
    """Gallery image attached to a service."""

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Услуга"),
    )
    image = models.ImageField(_("Изображение"), upload_to="services/gallery/")
    alt = models.CharField(_("Подпись"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Изображение услуги")
        verbose_name_plural = _("Изображения услуги")
        ordering = ["order", "id"]

    def __str__(self):
        return self.alt or f"#{self.pk}"

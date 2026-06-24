from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from catalog.models import unique_slug


class Project(models.Model):
    """A completed project for the «Наши работы» portfolio."""

    title = models.CharField(_("Название"), max_length=200)
    slug = models.SlugField(_("Слаг"), max_length=220, unique=True, blank=True)
    description = models.TextField(_("Описание"), blank=True)
    cover = models.ImageField(_("Обложка"), upload_to="projects/")
    location = models.CharField(_("Местоположение"), max_length=150, blank=True)
    year = models.CharField(_("Год"), max_length=10, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    is_active = models.BooleanField(_("Активен"), default=True)

    class Meta:
        verbose_name = _("Проект")
        verbose_name_plural = _("Наши работы")
        ordering = ["order", "-id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Project, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.slug])


class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="images", verbose_name=_("Проект"),
    )
    image = models.ImageField(_("Изображение"), upload_to="projects/gallery/")
    alt = models.CharField(_("Подпись"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Изображение проекта")
        verbose_name_plural = _("Изображения проекта")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.project.title} — {self.alt or self.pk}"

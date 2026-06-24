from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def unique_slug(model, value):
    """Build a slug unique within `model`. allow_unicode keeps Cyrillic readable."""
    base = slugify(value, allow_unicode=True) or "item"
    slug = base
    i = 2
    while model.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


class Color(models.Model):
    """A RAL colour, used both for the palette page and product colour options."""

    code = models.CharField(_("Код RAL"), max_length=20, unique=True)
    name = models.CharField(_("Название"), max_length=80, blank=True)
    hex = models.CharField(_("HEX"), max_length=7, help_text="#1166b3")

    class Meta:
        verbose_name = _("Цвет (RAL)")
        verbose_name_plural = _("Цвета (RAL)")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}".strip()


class Category(models.Model):
    """Catalog category. Self-referential `parent` enables sub-categories
    (e.g. Сэндвич-панели → Кровельные / Стеновые)."""

    name = models.CharField(_("Название"), max_length=150)
    slug = models.SlugField(_("Слаг"), max_length=170, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Родительская категория"),
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    description = models.TextField(_("Описание"), blank=True)
    image = models.ImageField(_("Изображение"), upload_to="categories/", blank=True)
    phone = models.CharField(
        _("Телефон направления"), max_length=40, blank=True,
        help_text=_("Например: +998 95 429-00-00"),
    )
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category", args=[self.slug])

    @property
    def is_root(self):
        return self.parent_id is None


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name=_("Категория"),
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(_("Название"), max_length=200)
    slug = models.SlugField(_("Слаг"), max_length=220, unique=True, blank=True)
    short_description = models.CharField(_("Краткое описание"), max_length=300, blank=True)
    description = models.TextField(_("Описание"), blank=True)
    main_image = models.ImageField(_("Главное изображение"), upload_to="products/", blank=True)
    colors = models.ManyToManyField(
        Color, verbose_name=_("Доступные цвета"), blank=True, related_name="products",
    )
    is_featured = models.BooleanField(_("Рекомендуемый"), default=False)
    is_active = models.BooleanField(_("Активен"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товары")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Product, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product", args=[self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images", verbose_name=_("Товар"),
    )
    image = models.ImageField(_("Изображение"), upload_to="products/gallery/")
    alt = models.CharField(_("Подпись"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Изображение товара")
        verbose_name_plural = _("Изображения товара")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.product.name} — {self.alt or self.pk}"


class ProductSpec(models.Model):
    """One row in a product's technical-characteristics table."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="specs", verbose_name=_("Товар"),
    )
    name = models.CharField(_("Характеристика"), max_length=150)
    value = models.CharField(_("Значение"), max_length=200)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Характеристика")
        verbose_name_plural = _("Характеристики")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.name}: {self.value}"

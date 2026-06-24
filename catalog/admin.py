from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline

from .models import Category, Color, Product, ProductImage, ProductSpec


@admin.register(Color)
class ColorAdmin(TabbedTranslationAdmin):
    list_display = ("code", "name", "swatch")
    search_fields = ("code", "name")

    @admin.display(description="")
    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:24px;height:24px;border:1px solid #ccc;'
            'background:{}"></span>',
            obj.hex or "#fff",
        )


@admin.register(Category)
class CategoryAdmin(TabbedTranslationAdmin):
    list_display = ("name", "parent", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name",)
    readonly_fields = ("slug",)


class ProductImageInline(TranslationStackedInline):
    model = ProductImage
    extra = 1


class ProductSpecInline(TranslationStackedInline):
    model = ProductSpec
    extra = 2


@admin.register(Product)
class ProductAdmin(TabbedTranslationAdmin):
    list_display = ("name", "category", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("name", "short_description")
    autocomplete_fields = ("category", "colors")
    readonly_fields = ("slug",)
    inlines = [ProductSpecInline, ProductImageInline]

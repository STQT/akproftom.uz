from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline

from .models import Service, ServiceGroup, ServiceImage


class ServiceImageInline(TranslationStackedInline):
    model = ServiceImage
    extra = 1


@admin.register(ServiceGroup)
class ServiceGroupAdmin(TabbedTranslationAdmin):
    list_display = ("title", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title",)
    readonly_fields = ("slug",)


@admin.register(Service)
class ServiceAdmin(TabbedTranslationAdmin):
    list_display = ("title", "group", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    list_filter = ("group", "is_featured", "is_active")
    search_fields = ("title", "short_description")
    autocomplete_fields = ("group",)
    readonly_fields = ("slug",)
    inlines = [ServiceImageInline]

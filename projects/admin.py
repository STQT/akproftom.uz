from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline

from .models import Project, ProjectImage


class ProjectImageInline(TranslationStackedInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(TabbedTranslationAdmin):
    list_display = ("title", "location", "year", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "location")
    readonly_fields = ("slug",)
    inlines = [ProjectImageInline]

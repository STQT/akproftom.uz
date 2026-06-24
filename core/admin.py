from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin

from .models import Certificate, Inquiry, Phone, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(TabbedTranslationAdmin):
    list_display = ("company_name", "email")

    def has_add_permission(self, request):
        # Singleton: forbid creating a second row.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Phone)
class PhoneAdmin(TabbedTranslationAdmin):
    list_display = ("number", "label", "order")
    list_editable = ("order",)


@admin.register(Certificate)
class CertificateAdmin(TabbedTranslationAdmin):
    list_display = ("__str__", "order")
    list_editable = ("order",)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "product", "is_processed", "created_at")
    list_editable = ("is_processed",)
    list_filter = ("is_processed", "created_at")
    search_fields = ("name", "phone", "message")
    readonly_fields = ("name", "phone", "message", "product", "source_url", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False  # inquiries are created by the public form only

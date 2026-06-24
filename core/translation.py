from modeltranslation.translator import TranslationOptions, register

from .models import Certificate, Phone, SiteSettings


@register(SiteSettings)
class SiteSettingsTR(TranslationOptions):
    fields = ("address", "work_hours", "about_text", "process_text")


@register(Phone)
class PhoneTR(TranslationOptions):
    fields = ("label",)


@register(Certificate)
class CertificateTR(TranslationOptions):
    fields = ("title",)

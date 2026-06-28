from modeltranslation.translator import TranslationOptions, register

from .models import Service, ServiceGroup, ServiceImage


@register(ServiceGroup)
class ServiceGroupTR(TranslationOptions):
    fields = ("title", "description")


@register(Service)
class ServiceTR(TranslationOptions):
    fields = ("title", "short_description", "description")


@register(ServiceImage)
class ServiceImageTR(TranslationOptions):
    fields = ("alt",)

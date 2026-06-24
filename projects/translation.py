from modeltranslation.translator import TranslationOptions, register

from .models import Project, ProjectImage


@register(Project)
class ProjectTR(TranslationOptions):
    fields = ("title", "description", "location")


@register(ProjectImage)
class ProjectImageTR(TranslationOptions):
    fields = ("alt",)

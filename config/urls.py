"""Root URL configuration.

The language switcher (set_language) lives outside i18n_patterns; all public
pages live inside it so every URL carries a /ru/ /uz/ /en/ prefix.
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, register_converter


class UnicodeSlugConverter:
    """Like the built-in `slug` converter but `\\w` matches Cyrillic too, so
    auto-generated Cyrillic slugs resolve and reverse correctly."""

    regex = r"[-\w]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(UnicodeSlugConverter, "uslug")

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # set_language endpoint
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("catalog.urls")),
    path("projects/", include("projects.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

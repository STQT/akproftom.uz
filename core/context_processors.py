from catalog.models import Category

from .forms import InquiryForm
from .models import Phone, SiteSettings


def site_globals(request):
    """Inject global content (settings, phones, nav categories, request form)
    into every template."""
    root_categories = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related("children")
    )
    return {
        "site": SiteSettings.get(),
        "phones": Phone.objects.all(),
        "nav_categories": root_categories,
        "inquiry_form": InquiryForm(),
    }

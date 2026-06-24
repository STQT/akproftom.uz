from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from catalog.models import Category, Color, Product
from projects.models import Project

from .forms import InquiryForm
from .models import Certificate


def home(request):
    categories = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related("children")
    )
    featured = list(Product.objects.filter(is_active=True, is_featured=True)[:8])
    if not featured:
        featured = list(Product.objects.filter(is_active=True)[:8])
    context = {
        "categories": categories,
        "featured_products": featured,
        "projects": Project.objects.filter(is_active=True)[:6],
        "certificates": Certificate.objects.all()[:6],
    }
    return render(request, "home.html", context)


def about(request):
    return render(request, "core/about.html", {
        "certificates": Certificate.objects.all(),
    })


def contacts(request):
    return render(request, "core/contacts.html")


def certificates(request):
    return render(request, "core/certificates.html", {
        "certificates": Certificate.objects.all(),
    })


def colors(request):
    return render(request, "core/colors.html", {
        "colors": Color.objects.all(),
    })


@require_POST
def inquiry_create(request):
    """Handle a «заявка» submission from any page and redirect back."""
    form = InquiryForm(request.POST)
    redirect_to = (
        request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or reverse("core:home")
    )
    # Guard against open-redirects / mangled targets.
    if not url_has_allowed_host_and_scheme(
        redirect_to, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        redirect_to = reverse("core:home")

    if form.is_spam():  # honeypot tripped — pretend success, save nothing
        messages.success(request, _("Спасибо! Ваша заявка отправлена."))
        return redirect(redirect_to)

    if form.is_valid():
        inquiry = form.save(commit=False)
        product_id = request.POST.get("product_id")
        if product_id:
            inquiry.product = Product.objects.filter(pk=product_id).first()
        inquiry.source_url = redirect_to[:300]
        inquiry.save()
        messages.success(
            request, _("Спасибо! Ваша заявка отправлена. Мы свяжемся с вами.")
        )
    else:
        messages.error(request, _("Проверьте правильность заполнения формы."))
    return redirect(redirect_to)

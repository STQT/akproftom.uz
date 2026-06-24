from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def index(request):
    """Catalog landing — all root categories with their sub-categories."""
    categories = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related("children")
    )
    return render(request, "catalog/index.html", {"categories": categories})


def category(request, slug):
    cat = get_object_or_404(Category, slug=slug, is_active=True)
    children = cat.children.filter(is_active=True)

    # Products of this category plus any of its sub-categories.
    cat_ids = [cat.id] + list(children.values_list("id", flat=True))
    products = (
        Product.objects.filter(category_id__in=cat_ids, is_active=True)
        .select_related("category")
    )
    context = {
        "category": cat,
        "children": children,
        "products": products,
        "breadcrumbs": _breadcrumbs(cat),
    }
    return render(request, "catalog/category.html", context)


def product(request, slug):
    item = get_object_or_404(
        Product.objects.select_related("category"), slug=slug, is_active=True
    )
    related = (
        Product.objects.filter(category=item.category, is_active=True)
        .exclude(pk=item.pk)[:4]
    )
    context = {
        "product": item,
        "specs": item.specs.all(),
        "gallery": item.images.all(),
        "colors": item.colors.all(),
        "related": related,
        "breadcrumbs": _breadcrumbs(item.category) + [(item.name, None)],
    }
    return render(request, "catalog/product.html", context)


def search(request):
    query = (request.GET.get("q") or "").strip()
    results = Product.objects.none()
    if query:
        results = (
            Product.objects.filter(is_active=True)
            .filter(
                Q(name__icontains=query)
                | Q(short_description__icontains=query)
                | Q(description__icontains=query)
            )
            .select_related("category")
        )
    return render(request, "catalog/search.html", {"query": query, "results": results})


def _breadcrumbs(cat):
    """Return [(label, url-or-None), …] from root category down to `cat`."""
    chain = []
    node = cat
    while node is not None:
        chain.append((node.name, node.get_absolute_url()))
        node = node.parent
    return list(reversed(chain))

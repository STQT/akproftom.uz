from django.shortcuts import get_object_or_404, render

from .models import Service, ServiceGroup


def service_list(request):
    """All active services, grouped under their headings. Services without a
    group (or whose group is inactive) fall into an «Прочие услуги» bucket."""
    groups = (
        ServiceGroup.objects.filter(is_active=True)
        .prefetch_related("services")
    )
    grouped = []
    for group in groups:
        items = list(group.services.filter(is_active=True))
        if items:
            grouped.append({"group": group, "services": items})

    ungrouped = list(Service.objects.filter(is_active=True, group__isnull=True))

    return render(request, "services/list.html", {
        "grouped": grouped,
        "ungrouped": ungrouped,
    })


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    related = (
        Service.objects.filter(is_active=True, group=service.group)
        .exclude(pk=service.pk)[:4]
        if service.group_id
        else []
    )
    return render(request, "services/detail.html", {
        "service": service,
        "gallery": service.images.all(),
        "related": related,
    })

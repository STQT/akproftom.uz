from django.db import migrations


# (slug, title, description) for the three service groups.
GROUPS = [
    (
        "mehanicheskaya-obrabotka",
        "Механическая обработка",
        "Полный цикл механической обработки металла на станочном парке.",
        10,
    ),
    (
        "svarochnye-raboty",
        "Сварочные работы",
        "Сварочные работы любой сложности — по чертежам и образцам.",
        20,
    ),
    (
        "specialnye-raboty",
        "Специальные работы",
        "Нестандартные и сложные работы по металлу.",
        30,
    ),
]

# (group_slug, slug, title, short_description, is_featured)
SERVICES = [
    ("mehanicheskaya-obrabotka", "tokarnaya-obrabotka", "Токарная обработка",
     "Изготовление деталей вращения: валы, втулки, фланцы, шкивы — по чертежам и образцам.", True),
    ("mehanicheskaya-obrabotka", "gilotina-rubka-metalla", "Гильотина для рубки металла",
     "Точная рубка листового металла на гильотинных ножницах.", True),
    ("mehanicheskaya-obrabotka", "valcevanie-metalla", "Вальцевание металла",
     "Вальцовка листа в обечайки и цилиндры заданного радиуса.", True),
    ("mehanicheskaya-obrabotka", "dolbezhnaya-strogalnaya-obrabotka", "Долбёжная и строгальная обработка",
     "Долбление шпоночных пазов, шлицев и строгание плоских поверхностей.", False),

    ("svarochnye-raboty", "elektro-dugovaya-svarka", "Электро-дуговая сварка",
     "Ручная дуговая сварка металлоконструкций и деталей.", True),
    ("svarochnye-raboty", "kempi-poluavtomat", "Кемпи (полуавтомат)",
     "Полуавтоматическая сварка Kemppi — аккуратный и прочный шов.", True),
    ("svarochnye-raboty", "argonnaya-svarka", "Аргонная сварка",
     "Аргонодуговая (TIG) сварка нержавеющей стали, алюминия и цветных металлов.", False),

    ("specialnye-raboty", "izgotovlenie-shesteren", "Изготовление шестерён",
     "Нарезка зубчатых колёс, шестерён и звёздочек по образцу или чертежу.", True),
    ("specialnye-raboty", "rastochnye-raboty", "Расточные работы",
     "Расточка отверстий и посадочных мест с высокой точностью.", False),
    ("specialnye-raboty", "sborochnye-raboty", "Сборочные работы",
     "Сборка узлов и нестандартного оборудования из готовых деталей.", False),
]


def seed(apps, schema_editor):
    ServiceGroup = apps.get_model("services", "ServiceGroup")
    Service = apps.get_model("services", "Service")

    group_by_slug = {}
    for slug, title, desc, order in GROUPS:
        group, _ = ServiceGroup.objects.get_or_create(
            slug=slug,
            defaults={
                "title": title,
                "title_ru": title,
                "description": desc,
                "description_ru": desc,
                "order": order,
                "is_active": True,
            },
        )
        group_by_slug[slug] = group

    for order, (group_slug, slug, title, short, featured) in enumerate(SERVICES, start=1):
        Service.objects.get_or_create(
            slug=slug,
            defaults={
                "group": group_by_slug.get(group_slug),
                "title": title,
                "title_ru": title,
                "short_description": short,
                "short_description_ru": short,
                "is_featured": featured,
                "is_active": True,
                "order": order * 10,
            },
        )


def unseed(apps, schema_editor):
    ServiceGroup = apps.get_model("services", "ServiceGroup")
    Service = apps.get_model("services", "Service")
    Service.objects.filter(slug__in=[s[1] for s in SERVICES]).delete()
    ServiceGroup.objects.filter(slug__in=[g[0] for g in GROUPS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]

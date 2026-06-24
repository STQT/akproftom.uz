"""Populate the database with demo content extracted from the company catalog.

Idempotent: safe to run multiple times (uses get_or_create / slug lookups and
only attaches an image when the field is still empty). Images are read from the
committed ``seed_assets/`` directory, so the PDF is not required at deploy time.

    python manage.py seed_catalog
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Color, Product, ProductSpec
from core.models import Certificate, Phone, SiteSettings
from projects.models import Project

SEED = Path(settings.BASE_DIR) / "seed_assets"

# RU→{uz,en} translation map produced by tools/build_messages pipeline.
try:
    TRANSLATIONS = json.loads(
        (Path(settings.BASE_DIR) / "locale_content.json").read_text(encoding="utf-8")
    )
except FileNotFoundError:
    TRANSLATIONS = {}


def t(ru, lang):
    """Translation of `ru` into `lang` (uz/en); falls back to the RU source."""
    return (TRANSLATIONS.get(ru) or {}).get(lang) or ru


def set_tr(obj, **fields):
    """Set a modeltranslation field's base + _ru/_uz/_en from a RU source value.

    Usage: set_tr(product, name="Профнастил С-8", short_description="…")
    """
    for field, ru in fields.items():
        setattr(obj, field, ru)
        setattr(obj, f"{field}_ru", ru)
        setattr(obj, f"{field}_uz", t(ru, "uz"))
        setattr(obj, f"{field}_en", t(ru, "en"))


# ---- RAL palette (representative subset) ----------------------------------
RAL = [
    ("RAL 1014", "Слоновая кость", "#e0c39a"),
    ("RAL 1015", "Светлая слоновая кость", "#e6d2b5"),
    ("RAL 1018", "Цинково-жёлтый", "#f3d22b"),
    ("RAL 2004", "Оранжевый", "#e25303"),
    ("RAL 3005", "Винно-красный", "#5e2129"),
    ("RAL 3009", "Оксид красный", "#642424"),
    ("RAL 3011", "Коричнево-красный", "#781f19"),
    ("RAL 3020", "Транспортный красный", "#cc0605"),
    ("RAL 5002", "Ультрамарин", "#20214f"),
    ("RAL 5005", "Сигнальный синий", "#1d4f8b"),
    ("RAL 5021", "Морская волна", "#07737a"),
    ("RAL 6002", "Лиственно-зелёный", "#27462c"),
    ("RAL 6005", "Зелёный мох", "#0f4336"),
    ("RAL 6029", "Мятно-зелёный", "#00794b"),
    ("RAL 7004", "Сигнальный серый", "#969696"),
    ("RAL 7024", "Графитовый серый", "#474a51"),
    ("RAL 8004", "Медно-коричневый", "#8e402a"),
    ("RAL 8017", "Шоколадно-коричневый", "#45322e"),
    ("RAL 9002", "Серо-белый", "#e7ebda"),
    ("RAL 9003", "Сигнальный белый", "#f4f4f4"),
    ("RAL 9005", "Чёрный янтарь", "#0a0a0a"),
    ("RAL 9006", "Бело-алюминиевый", "#a5a5a5"),
]


# ---- Categories: (slug, name_ru, name_uz, name_en, image, parent_slug, desc_ru) ----
CATEGORIES = [
    ("sandwich-paneli", "Сэндвич-панели", "Sendvich-panellar", "Sandwich panels",
     "sandwich_stack.jpg", None,
     "Кровельные и стеновые сэндвич-панели с утеплителем из минеральной ваты. "
     "Собственное производство на линии Dai San (Корея)."),
    ("krovelnye-sendvich-paneli", "Кровельные сэндвич-панели", "Tom sendvich-panellari",
     "Roof sandwich panels", "sandwich_roof.jpg", "sandwich-paneli",
     "Замковое соединение Roof-Lock обеспечивает стопроцентную влагонепроницаемость кровли."),
    ("stenovye-sendvich-paneli", "Стеновые сэндвич-панели", "Devor sendvich-panellari",
     "Wall sandwich panels", "sandwich_wall.jpg", "sandwich-paneli",
     "Замок Z-Lock. Профили: Стандарт, Микро (SilkLine), Гладкий, V-образный."),
    ("profnastil", "Профнастил", "Profnastil", "Corrugated sheet",
     "prof_c8.jpg", None,
     "Стальные профилированные листы С-8, С-18, С-20, НС-35, НС-44, НС-60, Н-75 "
     "для кровли, стен и несущих конструкций."),
    ("list", "Лист", "Prokat list", "Steel sheet",
     "list_stack.jpg", None,
     "Стальной горячекатаный и холоднокатаный лист различной толщины со склада и под заказ."),
    ("armatura", "Арматура", "Armatura", "Rebar",
     "armatura_a1.jpg", None,
     "Арматура классов А-1 и А-2 для железобетонных конструкций."),
    ("profil-shtrips", "Профиль штрипс", "Shtrips profil", "Steel strip",
     "", None,
     "Стальная лента (штрипс) для производства профилей и доборных элементов."),
    ("metallokonstrukcii", "Металлоконструкции", "Metall konstruksiyalar",
     "Metal structures", "project_6.jpg", None,
     "Изготовление и монтаж металлоконструкций любой сложности: каркасы, фермы, ангары."),
    ("dobornye-elementy", "Доборные элементы", "Qo‘shimcha elementlar",
     "Flashings & trims", "", None,
     "Нащельники, коньки, отливы, парапеты и другие доборные элементы из оцинкованной стали."),
]


# ---- Products: dict per item ----------------------------------------------
PRODUCTS = [
    dict(slug="krovelnaya-sendvich-panel", cat="krovelnye-sendvich-paneli",
         name="Кровельная сэндвич-панель", name_en="Roof sandwich panel",
         short="Трёхслойная кровельная панель с минеральной ватой, замок Roof-Lock.",
         image="sandwich_roof.jpg", featured=True, colors=True,
         specs=[("Монтажная ширина", "1000 мм"), ("Толщина панели", "50–125 мм"),
                ("Масса 1 м²", "17,0–24,5 кг"), ("Макс. длина", "12000 мм"),
                ("Утеплитель", "Минеральная вата, λ=0,041 Вт/(м·°С)"),
                ("Замок", "Roof-Lock")]),
    dict(slug="stenovaya-sendvich-panel", cat="stenovye-sendvich-paneli",
         name="Стеновая сэндвич-панель", name_en="Wall sandwich panel",
         short="Стеновая панель с замком Z-Lock, профилирование Стандарт/Микро/Гладкий/V.",
         image="sandwich_wall.jpg", featured=True, colors=True,
         specs=[("Монтажная ширина", "1000 мм"), ("Толщина панели", "50–120 мм"),
                ("Масса 1 м²", "14,0–21,5 кг"), ("Макс. длина", "12000 мм"),
                ("Утеплитель", "Минеральная вата, λ=0,041 Вт/(м·°С)"),
                ("Замок", "Z-Lock")]),
    dict(slug="profnastil-s-8", cat="profnastil", name="Профнастил С-8",
         name_en="Corrugated sheet C-8",
         short="Стеновой профнастил с высотой профиля 8 мм для облицовки и заборов.",
         image="prof_c8.jpg", featured=True, colors=True,
         specs=[("Высота профиля", "8 мм"), ("Толщина стали", "0,4–0,7 мм"),
                ("Назначение", "Стены, заборы, облицовка"), ("Длина", "По заказу")]),
    dict(slug="profnastil-s-18", cat="profnastil", name="Профнастил С-18",
         name_en="Corrugated sheet C-18",
         short="Универсальный профнастил С-18 для кровли и стен.",
         image="prof_c18.jpg", featured=False, colors=True,
         specs=[("Высота профиля", "18 мм"), ("Габаритная ширина", "1150 мм"),
                ("Толщина стали", "0,4–0,7 мм"), ("Длина", "По заказу")]),
    dict(slug="profnastil-s-20", cat="profnastil", name="Профнастил С-20",
         name_en="Corrugated sheet C-20",
         short="Профнастил С-20 для кровли, стен и ограждений.",
         image="prof_c20.jpg", featured=True, colors=True,
         specs=[("Высота профиля", "20 мм"), ("Рабочая ширина", "1100 мм"),
                ("Толщина стали", "0,4–0,8 мм"), ("Длина", "По заказу")]),
    dict(slug="profnastil-ns-60", cat="profnastil", name="Профнастил НС-60",
         name_en="Corrugated sheet NS-60",
         short="Несуще-стеновой профиль НС-60 для кровли и перекрытий.",
         image="prof_ns60.jpg", featured=False, colors=True,
         specs=[("Высота профиля", "60 мм"), ("Габаритная ширина", "902 мм"),
                ("Рабочая ширина", "845 мм"), ("Толщина стали", "0,5–0,9 мм")]),
    dict(slug="profnastil-n-75", cat="profnastil", name="Профнастил Н-75",
         name_en="Load-bearing sheet N-75",
         short="Несущий профнастил Н-75 для кровли и несъёмной опалубки.",
         image="prof_n75.jpg", featured=False, colors=True,
         specs=[("Высота профиля", "75 мм"), ("Габаритная ширина", "800 мм"),
                ("Рабочая ширина", "750 мм"), ("Толщина стали", "0,7–1,0 мм")]),
    dict(slug="list-stalnoy", cat="list", name="Лист стальной",
         name_en="Steel sheet",
         short="Горячекатаный и холоднокатаный стальной лист различной толщины.",
         image="list_yard.jpg", featured=False, colors=False,
         specs=[("Тип", "Горячекатаный / холоднокатаный"),
                ("Толщина", "1–20 мм"), ("Размеры", "По ГОСТ / под заказ")]),
    dict(slug="armatura-a1", cat="armatura", name="Арматура А-1",
         name_en="Rebar A-1",
         short="Гладкая арматура класса А-1 для железобетонных конструкций.",
         image="armatura_a1.jpg", featured=False, colors=False,
         specs=[("Класс", "А-1 (А240)"), ("Поверхность", "Гладкая"),
                ("Диаметр", "6–40 мм")]),
    dict(slug="armatura-a2", cat="armatura", name="Арматура А-2",
         name_en="Rebar A-2",
         short="Рифлёная арматура класса А-2 для армирования бетона.",
         image="armatura_a2.jpg", featured=False, colors=False,
         specs=[("Класс", "А-2 (А300)"), ("Поверхность", "Рифлёная"),
                ("Диаметр", "10–40 мм")]),
    dict(slug="profil-shtrips", cat="profil-shtrips", name="Профиль штрипс",
         name_en="Steel strip",
         short="Стальная лента (штрипс) с полимерным и цинковым покрытием.",
         image="", featured=False, colors=True,
         specs=[("Толщина", "0,4–1,0 мм"), ("Ширина", "По заказу"),
                ("Покрытие", "Оцинковка / полимер")]),
]


# ---- Projects --------------------------------------------------------------
PROJECTS = [
    ("Производственный корпус", "Tashkent", "2023", "project_1.jpg"),
    ("Складской комплекс", "Tashkent", "2023", "project_2.jpg"),
    ("Торговый павильон", "Tashkent", "2022", "project_3.jpg"),
    ("Логистический центр", "Samarkand", "2022", "project_4.jpg"),
    ("Кровля промышленного здания", "Tashkent", "2021", "project_5.jpg"),
    ("Металлокаркас ангара", "Tashkent", "2021", "project_6.jpg"),
]

CERTIFICATES = [
    ("Сертификат соответствия (сэндвич-панели)", "cert_1.jpg"),
    ("Сертификат соответствия (профнастил)", "cert_2.jpg"),
]

PHONES = [
    ("+998 95 429-00-00", "Сэндвич-панели"),
    ("+998 95 422-11-11", "Сэндвич-панели"),
    ("+998 98 360-60-97", "Профнастил"),
    ("+998 95 004-55-55", "Профнастил"),
    ("+998 77 010-00-00", "Лист, арматура"),
    ("+998 93 100-00-06", "Лист, арматура"),
    ("+998 99 943-08-80", "Профиль штрипс"),
]

# --- Site settings (non-translatable + translatable RU source values) ---
COMPANY_NAME = "TASHKENT PROFNASTIL SERVIS"
EMAIL = "info@akproftom.uz"
ADDRESS = "г. Ташкент, Зангиатинский район"
WORK_HOURS = "Пн–Сб, 9:00–18:00"
ABOUT_TEXT = (
    "ООО «TASHKENT PROFNASTIL SERVIS» — современное промышленное предприятие, "
    "основанное в 2017 году, занятое в сфере заготовительного производства, "
    "металлоконструкций, сэндвич-панелей, а также гранитных и мраморных плит "
    "для отраслей промышленного и жилищного строительства, общественных зданий "
    "и сооружений.\n\nПредприятие располагает современной технологической линией "
    "от компании Dai San Industrial Co. Ltd (Южная Корея) на площадях 4500 м². "
    "Мощность производства — более 1 млн м² кровельных и стеновых сэндвич-панелей "
    "с утеплителем из минеральной ваты в год."
)
PROCESS_TEXT = (
    "Панели изготавливаются непрерывным способом на автоматической линии, "
    "обеспечивающей полный контроль над производством и стабильно высокое "
    "качество. Управление осуществляется современным компьютерным процессором "
    "в режиме реального времени."
)


def attach(field, filename):
    """Attach a seed image to an ImageField if the file exists and field empty."""
    if not filename:
        return False
    path = SEED / filename
    if path.exists() and not field:
        field.save(filename, File(path.open("rb")), save=False)
        return True
    return False


class Command(BaseCommand):
    help = "Seed demo catalog content (categories, products, projects, etc.)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding catalog…")
        self._colors()
        self._settings()
        self._phones()
        cats = self._categories()
        self._products(cats)
        self._projects()
        self._certificates()
        self.stdout.write(self.style.SUCCESS("Done. Catalog seeded."))

    # -- colours --
    def _colors(self):
        for code, name, hexv in RAL:
            c, _ = Color.objects.get_or_create(code=code, defaults={"hex": hexv})
            c.hex = c.hex or hexv
            set_tr(c, name=name)
            c.save()
        self.stdout.write(f"  colors: {Color.objects.count()}")

    # -- site settings --
    def _settings(self):
        s = SiteSettings.get()
        s.company_name = COMPANY_NAME
        s.email = s.email or EMAIL
        s.telegram = s.telegram or "https://t.me/"
        s.instagram = s.instagram or "https://instagram.com/"
        set_tr(s, address=ADDRESS, work_hours=WORK_HOURS,
               about_text=ABOUT_TEXT, process_text=PROCESS_TEXT)
        s.save()
        self.stdout.write("  site settings: ok")

    # -- phones --
    def _phones(self):
        for i, (num, label) in enumerate(PHONES):
            ph, _ = Phone.objects.get_or_create(number=num, defaults={"order": i})
            set_tr(ph, label=label)
            ph.save()
        self.stdout.write(f"  phones: {Phone.objects.count()}")

    # -- categories --
    def _categories(self):
        cats = {}
        for i, (slug, ru, uz, en, img, parent, desc) in enumerate(CATEGORIES):
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={"order": i})
            cat.parent = cats.get(parent) if parent else None
            cat.order = i
            cat.is_active = True
            set_tr(cat, name=ru, description=desc)
            if not cat.image:
                attach(cat.image, img)
            cat.save()
            cats[slug] = cat
        self.stdout.write(f"  categories: {Category.objects.count()}")
        return cats

    # -- products --
    def _products(self, cats):
        for i, p in enumerate(PRODUCTS):
            prod, _ = Product.objects.get_or_create(
                slug=p["slug"], defaults={"category": cats[p["cat"]], "order": i},
            )
            prod.category = cats[p["cat"]]
            prod.is_featured = p.get("featured", False)
            prod.order = i
            prod.is_active = True
            set_tr(prod, name=p["name"], short_description=p["short"])
            if not prod.main_image:
                attach(prod.main_image, p.get("image", ""))
            prod.save()
            # Rebuild specs so translations apply on re-run.
            prod.specs.all().delete()
            for j, (n, v) in enumerate(p.get("specs", [])):
                spec = ProductSpec(product=prod, order=j)
                set_tr(spec, name=n, value=v)
                spec.save()
            if p.get("colors"):
                prod.colors.set(Color.objects.all()[:12])
        self.stdout.write(f"  products: {Product.objects.count()}")

    # -- projects --
    def _projects(self):
        for i, (title, loc, year, img) in enumerate(PROJECTS):
            slug = slugify(title, allow_unicode=True)
            proj, _ = Project.objects.get_or_create(slug=slug, defaults={"order": i})
            proj.location = loc
            proj.year = year
            proj.order = i
            proj.is_active = True
            set_tr(proj, title=title)
            if not proj.cover:
                attach(proj.cover, img)
            proj.save()
        self.stdout.write(f"  projects: {Project.objects.count()}")

    # -- certificates --
    def _certificates(self):
        for i, (title, img) in enumerate(CERTIFICATES):
            cert, _ = Certificate.objects.get_or_create(title=title, defaults={"order": i})
            set_tr(cert, title=title)
            if not cert.image:
                attach(cert.image, img)
            cert.save()
        self.stdout.write(f"  certificates: {Certificate.objects.count()}")

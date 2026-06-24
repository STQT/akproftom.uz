# akproftom.uz — сайт-каталог TASHKENT PROFNASTIL SERVIS

Каталог металлопродукции (сэндвич-панели, профнастил, лист, арматура, штрипс,
металлоконструкции) на **Django (MVT)** с трёхъязычным интерфейсом (RU / UZ / EN)
и формой «заявка на расчёт» вместо публичных цен.

## Стек

- Django 5.2 LTS · django-modeltranslation (переводимые поля) · django-environ
- Pillow · WhiteNoise (статика) · PyMySQL (MySQL на проде), SQLite (локально)

## Локальный запуск (Windows / PowerShell или bash)

```bash
python -m venv venv
venv\Scripts\activate            # PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt

# .env уже настроен на SQLite + DEBUG=True для разработки
python manage.py migrate
python manage.py seed_catalog        # демо-данные + изображения из seed_assets/
python manage.py createsuperuser
python manage.py runserver
```

Откройте http://127.0.0.1:8000/ — произойдёт редирект на `/ru/`.
Админка: http://127.0.0.1:8000/admin/

## Структура

| Приложение | Содержимое |
|-----------|-----------|
| `core`    | главная, о компании, контакты, сертификаты, RAL, форма заявки, `SiteSettings` |
| `catalog` | категории (с подкатегориями), товары, характеристики, галерея, RAL-цвета |
| `projects`| портфолио «Наши работы» |

Маршруты живут внутри `i18n_patterns` (префиксы `/ru/ /uz/ /en/`).
Переводимые поля моделей помечены в `*/translation.py`.

## Контент

- Управление через `/admin/` (товары, категории, проекты, телефоны, настройки).
- Заявки клиентов: админка → **Заявки**.
- Демо-наполнение: `python manage.py seed_catalog` (идемпотентно).

## Переводы (i18n) — RU / UZ / EN

Сайт переведён на три языка: **статика** (надписи интерфейса) и **динамика**
(контент моделей).

- **Источник переводов** — [locale_content.json](locale_content.json):
  `{"<русская строка>": {"uz": "...", "en": "..."}}`. Один файл для UI и контента.
- **Статика** (кнопки, меню, заголовки): строки в шаблонах помечены `{% trans %}`.
  После правки `locale_content.json` пересоберите каталоги командой
  `python tools/build_messages.py` — она пишет `locale/<lang>/LC_MESSAGES/django.po`
  и **компилирует `.mo` на чистом Python** (GNU gettext не требуется — удобно на Windows/cPanel).
- **Динамика** (категории, товары, характеристики, проекты, сертификаты, цвета,
  «О компании»): хранится в БД в полях `_ru/_uz/_en` (django-modeltranslation).
  Команда `python manage.py seed_catalog` идемпотентно проставляет переводы из
  `locale_content.json` на существующие записи. Точечно править удобнее в админке
  (у переводимых полей — вкладки RU/UZ/EN).

Добавить/исправить перевод: отредактируйте `locale_content.json` →
`python tools/build_messages.py` → `python manage.py seed_catalog` → перезапуск.

## Деплой

См. **[README_DEPLOY.md](README_DEPLOY.md)** — пошагово для cPanel (Setup Python App + MySQL).

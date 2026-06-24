# Деплой на cPanel (Setup Python App / Passenger)

Сайт-каталог **akproftom.uz** на Django 4.2/5.2 LTS. Прод-БД — **MySQL**,
статика — через **WhiteNoise**, медиа — отдаётся Apache из `public_html/media`.

> Требуется Python **3.10+** в cPanel (Setup Python App → выбор версии).

---

## 1. Создать базу MySQL

cPanel → **MySQL® Databases**:
1. Создайте базу, напр. `cpuser_akproftom`.
2. Создайте пользователя и пароль.
3. Добавьте пользователя к базе с привилегией **ALL PRIVILEGES**.

Запомните: имя БД, пользователь, пароль (понадобятся в env).

## 2. Загрузить файлы проекта

Загрузите проект в домашний каталог, напр. `/home/cpuser/akproftom`
(через cPanel **Git Version Control**, File Manager или FTP).
Каталог приложения держим **вне** `public_html`.

Не загружайте `venv/`, `db.sqlite3`, `staticfiles/`, `.env` — они для локалки
(см. `.gitignore`). Папку `seed_assets/` **загрузить нужно** (демо-изображения).

## 3. Создать Python-приложение

cPanel → **Setup Python App** → **Create Application**:

| Поле | Значение |
|------|----------|
| Python version | 3.10+ |
| Application root | `akproftom` |
| Application URL | `akproftom.uz` |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |

Создастся виртуальное окружение. Скопируйте показанную команду
`source /home/cpuser/virtualenv/akproftom/3.x/bin/activate` — пригодится в SSH.

## 4. Переменные окружения

В том же экране Python App добавьте **Environment variables**:

```
SECRET_KEY            = <длинная случайная строка>
DEBUG                 = False
ALLOWED_HOSTS         = akproftom.uz,www.akproftom.uz
CSRF_TRUSTED_ORIGINS  = https://akproftom.uz,https://www.akproftom.uz
DB_ENGINE             = mysql
DB_NAME               = cpuser_akproftom
DB_USER               = cpuser_akprof
DB_PASSWORD           = <пароль БД>
DB_HOST               = localhost
DB_PORT               = 3306
MEDIA_ROOT            = /home/cpuser/public_html/media
```

(Замените `cpuser` на ваш cPanel-логин.)

## 5. Установить зависимости

В экране Python App: поле **requirements.txt** → **Run Pip Install**.
Либо по SSH:

```bash
source /home/cpuser/virtualenv/akproftom/3.x/bin/activate
cd ~/akproftom
pip install -r requirements.txt
```

## 6. Миграции, статика, данные, админ

По SSH (venv активирован):

```bash
cd ~/akproftom
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_catalog          # демо-каталог из seed_assets/
python manage.py createsuperuser       # доступ в /admin/
```

## 7. Статика и медиа

- **Статика** (`/static/…`): отдаёт WhiteNoise из приложения после `collectstatic`.
  Отдельная настройка Apache не нужна.
- **Медиа** (`/media/…`, загрузки из админки): отдаёт Apache напрямую.
  Поэтому `MEDIA_ROOT` указывает в `public_html/media`. Создайте папку и убедитесь,
  что `collectstatic`/seed записали туда изображения (или перенесите `media/`):

```bash
mkdir -p ~/public_html/media
# если медиа уже легли в ~/akproftom/media — перенесите:
cp -r ~/akproftom/media/* ~/public_html/media/ 2>/dev/null || true
```

> Альтернатива: оставить `MEDIA_ROOT` в каталоге приложения и сделать симлинк
> `ln -s ~/akproftom/media ~/public_html/media`.

## 8. Перезапуск

Кнопка **Restart** в Setup Python App (или `touch ~/akproftom/tmp/restart.txt`).

Откройте `https://akproftom.uz` — главная должна открыться, `/admin/` — вход в админку.

---

## Обновление сайта

```bash
source /home/cpuser/virtualenv/akproftom/3.x/bin/activate
cd ~/akproftom
git pull                          # или загрузка новых файлов
pip install -r requirements.txt   # если менялись зависимости
python manage.py migrate
python manage.py collectstatic --noinput
# Restart в Setup Python App
```

## Заметки

- **Языки (RU/UZ/EN)**: переводы UI и контента уже готовы и закоммичены
  (`locale/*/LC_MESSAGES/django.mo`, `locale_content.json`). GNU gettext на сервере
  **не нужен**. Чтобы изменить перевод: правьте `locale_content.json` →
  `python tools/build_messages.py` (пересоберёт `.mo` на чистом Python) →
  `python manage.py seed_catalog` (обновит переводы контента в БД) → Restart.
  Контент также правится точечно в админке (вкладки RU/UZ/EN у переводимых полей).
  Убедитесь, что папка `locale/` загружена на сервер.
- **Заявки** клиентов копятся в админке → раздел **Заявки** (`core.Inquiry`).
- **SQLite для локалки**: оставьте `DB_ENGINE=sqlite` в `.env` — на проде MySQL.
- **HTTPS**: при включённом SSL Django выставляет secure-cookie (см. блок в `settings.py`).

# Деплой на cPanel (Setup Python App / Passenger)

Сайт-каталог **akproftom.uz** на Django 4.2/5.2 LTS. Прод-БД — **MySQL**;
статика и медиа — на **Cloudflare R2** (рекомендуется) либо локально
(WhiteNoise + Apache). Есть **Telegram-бот** (каталог в чате + уведомления о заявках).

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
USE_HTTPS             = True
DB_ENGINE             = mysql
DB_NAME               = cpuser_akproftom
DB_USER               = cpuser_akprof
DB_PASSWORD           = <пароль БД>
DB_HOST               = localhost
DB_PORT               = 3306
MEDIA_ROOT            = /home/cpuser/public_html/media
```

(Замените `cpuser` на ваш cPanel-логин. `MEDIA_ROOT` нужен только если медиа на
диске, а не в R2 — см. раздел 7.)

> ⚠️ **Не добавляйте комментарии `#` в той же строке, что и значение** —
> `.env` сохранит их как часть значения (напр. `TELEGRAM_WEBAPP_URL` с `#` сломает
> кнопку Mini App). Комментарии — только на отдельных строках.

**Медиа/статика на Cloudflare R2** (опционально — рекомендуется для прода).
Добавьте, если используете R2 (см. раздел 7):

```
USE_R2                = True
R2_ACCESS_KEY_ID      = <access key>
R2_SECRET_ACCESS_KEY  = <secret key>
R2_BUCKET             = akproftom
R2_ENDPOINT_URL       = https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_PUBLIC_URL         = https://pub-xxxxxxxx.r2.dev
```

> ⚠️ В `R2_ENDPOINT_URL` **не** добавляйте имя бакета — только `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.
> Имя бакета задаётся отдельно в `R2_BUCKET`. Иначе ключи получат лишний префикс и медиа отдаст 404.

**Telegram-бот и уведомления** (опционально — см. раздел 9):

```
TELEGRAM_BOT_TOKEN      = <токен от @BotFather>
TELEGRAM_CHAT_ID        = <chat_id для заявок>
TELEGRAM_WEBHOOK_SECRET = <случайная строка, A-Za-z0-9_- , 1-256 символов>
TELEGRAM_WEBHOOK_BASE   = https://akproftom.uz
TELEGRAM_WEBAPP_URL     = https://akproftom.uz
```

`TELEGRAM_CHAT_ID` может быть один id или несколько через запятую.
`TELEGRAM_WEBAPP_URL` — URL Mini App (кнопка «Открыть сайт»); оставьте пустым,
пока нет SSL. Значения пишите **без** inline-комментариев `#`.

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

Два варианта. **Рекомендуется R2** (вариант A).

### Вариант A — Cloudflare R2 (рекомендуется)

И статика, и медиа хранятся в одном R2-бакете (S3-совместимый), под префиксами
`static/` и `media/`. Подходит для прода: разгружает хостинг и CDN-отдача.

Настройка на стороне Cloudflare:
1. **R2 → Create bucket**, напр. `akproftom`.
2. На бакете включите **Public Development URL** (`https://pub-xxxx.r2.dev`) или
   привяжите кастомный домен (`https://media.akproftom.uz`).
3. **Manage API Tokens** → токен с правами **Object Read & Write** → получите
   Access Key ID, Secret Access Key и **endpoint** `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.
4. Заполните `USE_R2`, `R2_*` в env (см. раздел 4).

Затем:

```bash
python manage.py collectstatic --noinput   # зальёт статику в R2 (static/)
python manage.py seed_catalog              # картинки каталога уйдут в R2 (media/)
python manage.py r2_audit                  # проверка: ключи vs URL, всё должно быть OK
```

### Вариант B — локальный диск + Apache

- **Статика** (`/static/…`): отдаёт WhiteNoise из приложения после `collectstatic`.
- **Медиа** (`/media/…`): отдаёт Apache из `public_html/media` (`MEDIA_ROOT`):

```bash
mkdir -p ~/public_html/media
cp -r ~/akproftom/media/* ~/public_html/media/ 2>/dev/null || true
```

> Альтернатива: оставить `MEDIA_ROOT` в каталоге приложения и сделать симлинк
> `ln -s ~/akproftom/media ~/public_html/media`.

## 8. SSL (HTTPS)

cPanel → **SSL/TLS Status** → **Run AutoSSL** (бесплатный Let's Encrypt) для
`akproftom.uz` и `www.akproftom.uz`.

- До установки сертификата временно ставьте `USE_HTTPS=False` — иначе CSRF/сессионные
  cookie помечаются как HTTPS-only и форма заявки падает с CSRF-ошибкой по HTTP.
- После установки SSL верните `USE_HTTPS=True` (или уберите переменную — по умолчанию `True`)
  и перезапустите приложение.

> Telegram-бот и Mini App (раздел 9) **требуют рабочий HTTPS** — без SSL не заработают.

## 9. Перезапуск

Кнопка **Restart** в Setup Python App (или `touch ~/akproftom/tmp/restart.txt`).

Откройте `https://akproftom.uz` — главная должна открыться, `/admin/` — вход в админку.

## 10. Telegram-бот и уведомления

Бот делает три вещи: **шлёт заявки с сайта** в Telegram, даёт **каталог прямо в чате**
(категории → товары → заявка) и кнопку **Mini App** «Открыть сайт». Работает
**только в личных чатах** — группы/каналы игнорируются.

> **Важно:** на cPanel нет постоянного процесса, поэтому бот работает через
> **webhook** (Django-view), а не поллинг. Webhook и Mini App **требуют HTTPS** —
> сначала включите SSL (раздел 8).

### Только уведомления о заявках (без интерактивного бота)

Достаточно двух переменных — заявки с сайта будут приходить в чат:

```
TELEGRAM_BOT_TOKEN = <токен от @BotFather>
TELEGRAM_CHAT_ID   = <ваш chat_id>      # узнать: @userinfobot; для группы id вида -100…
```

Проверка: `python manage.py telegram_test`.

> Бот не может писать первым: в личке один раз нажмите **Start** у бота
> (или добавьте его в нужный чат).

### Полный бот (каталог в чате + Mini App)

1. У **@BotFather**: создайте бота, возьмите токен. Выполните
   `/setjoingroups` → **Disable** (запрет добавления в группы).
2. Заполните в env (раздел 4): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
   `TELEGRAM_WEBHOOK_SECRET` (длинная случайная строка),
   `TELEGRAM_WEBHOOK_BASE=https://akproftom.uz`,
   `TELEGRAM_WEBAPP_URL=https://akproftom.uz`.
3. Примените миграции и зарегистрируйте webhook:

```bash
python manage.py migrate           # таблица BotDialog (состояние диалога)
# Restart приложения, затем:
python manage.py set_webhook       # регистрирует webhook + команды бота
```

4. Напишите боту `/start` → должно открыться меню с каталогом.
   Кнопка «🌐 Открыть сайт» (Mini App) появляется автоматически при заданном
   `TELEGRAM_WEBAPP_URL`.

Управление webhook:

| Команда | Действие |
|---------|----------|
| `python manage.py set_webhook` | Зарегистрировать webhook и команды |
| `python manage.py delete_webhook` | Снять webhook (напр. для локальной отладки) |
| `python manage.py telegram_test` | Отправить тестовое сообщение в чат |

Эндпоинт webhook: `POST /telegram/webhook/` — защищён секрет-токеном
(`X-Telegram-Bot-Api-Secret-Token`), запросы без верного секрета получают 403.

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
- **Заявки** клиентов копятся в админке → раздел **Заявки** (`core.Inquiry`),
  а также приходят в Telegram (если настроен бот — раздел 10).
- **SQLite для локалки**: оставьте `DB_ENGINE=sqlite` в `.env` — на проде MySQL.
- **HTTPS**: управляется `USE_HTTPS` (раздел 8). При `True` Django выставляет
  secure-cookie; до установки SSL держите `False`.
- **R2**: при `USE_R2=True` медиа и статика уходят в Cloudflare R2 (раздел 7).
  Диагностика ключей/URL — `python manage.py r2_audit`.
- **Telegram-бот**: webhook + Mini App требуют HTTPS; только личные чаты
  (раздел 10).

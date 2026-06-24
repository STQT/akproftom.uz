"""
Django settings for TASHKENT PROFNASTIL SERVIS catalog (akproftom.uz).

Configuration is environment-driven (see .env.example). Local development
defaults to SQLite; production on cPanel uses MySQL — toggled via DB_ENGINE.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment -----------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["*"]),
    DB_ENGINE=(str, "sqlite"),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
# Read a .env file if present (not required — env vars can be set in cPanel).
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-dev-only-change-me-in-production-akproftom",
)
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")


# --- Applications ----------------------------------------------------------
INSTALLED_APPS = [
    "modeltranslation",  # must precede django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "catalog",
    "projects",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # i18n URL prefixes
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "core.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database --------------------------------------------------------------
if env("DB_ENGINE") == "mysql":
    # PyMySQL acts as the MySQLdb driver (pure-python, easy on cPanel).
    import pymysql

    pymysql.install_as_MySQLdb()
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --- Password validation ---------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalization --------------------------------------------------
LANGUAGE_CODE = "ru"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("ru", "Русский"),
    ("uz", "O‘zbekcha"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = "ru"
MODELTRANSLATION_LANGUAGES = ("ru", "uz", "en")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("ru", "uz", "en")


# --- Static & media --------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# Files: local filesystem + WhiteNoise by default; Cloudflare R2 (S3-compatible)
# in production when USE_R2=True. With R2 on, both media and static live in the
# same bucket under "media/" and "static/" prefixes.
USE_R2 = env.bool("USE_R2", default=False)

if USE_R2:
    AWS_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("R2_BUCKET")
    # R2 endpoint: https://<ACCOUNT_ID>.r2.cloudflarestorage.com
    AWS_S3_ENDPOINT_URL = env("R2_ENDPOINT_URL")
    # Public base URL for serving files (R2 public bucket or custom domain),
    # e.g. https://pub-xxxx.r2.dev or https://media.akproftom.uz — no scheme in
    # AWS_S3_CUSTOM_DOMAIN, so strip it.
    AWS_S3_CUSTOM_DOMAIN = (
        env("R2_PUBLIC_URL", default="")
        .replace("https://", "")
        .replace("http://", "")
        .rstrip("/")
    ) or None
    AWS_S3_REGION_NAME = "auto"          # R2 ignores region but boto3 needs a value
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = None                # R2 has no ACLs
    AWS_QUERYSTRING_AUTH = False          # public, clean URLs (no signed params)
    AWS_S3_FILE_OVERWRITE = False         # keep distinct uploads with same name
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "public, max-age=31536000"}

    # URLs become https://<R2_PUBLIC_URL>/media/... and /static/...
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/" if AWS_S3_CUSTOM_DOMAIN else "static/"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {"location": "media"},
        },
        "staticfiles": {
            # Manifest variant => hashed filenames for cache-busting on R2.
            "BACKEND": "storages.backends.s3.S3ManifestStaticStorage",
            "OPTIONS": {"location": "static"},
        },
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Telegram notifications (site inquiries) -------------------------------
# When both are set, new «заявки» are pushed to the chat(s). TELEGRAM_CHAT_ID
# may be a single id or a comma-separated list.
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", default="")


# --- Production hardening (applied when DEBUG is off) -----------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "SAMEORIGIN"

    # Secure cookies require HTTPS — if the cert isn't installed yet, the CSRF
    # cookie won't be sent over plain HTTP and the «заявка» form fails CSRF.
    # Keep USE_HTTPS=False until SSL is live, then switch it to True.
    USE_HTTPS = env.bool("USE_HTTPS", default=True)
    SESSION_COOKIE_SECURE = USE_HTTPS
    CSRF_COOKIE_SECURE = USE_HTTPS

    if not USE_HTTPS:
        # Allow POSTs from the plain-HTTP origin while running without SSL.
        CSRF_TRUSTED_ORIGINS += [
            f"http://{h}" for h in ALLOWED_HOSTS if h not in ("*", "")
        ]

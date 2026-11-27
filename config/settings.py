import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

from config.security import env_bool, validate_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# Helyi fejlesztésnél a .env fájlból jönnek a beállítások (a már beállított környezeti változók elsőbbséget élveznek).
load_dotenv(os.environ.get("DOTENV_FILE", BASE_DIR / ".env"))

DEBUG = os.environ.get("DEBUG", "0") == "1"

SECRET_KEY = os.environ.get("SECRET_KEY", "")
validate_secret_key(SECRET_KEY, DEBUG)
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-key-change-me"

ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]
# HTTPS-en át elérhető oldalnál (pl. alagút vagy hosting) a bejelentkezés/regisztráció POST-jaihoz kell.
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "listings",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "hu"

TIME_ZONE = "Europe/Belgrade"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Az OSM-csempeszerver Referer nélkül 403-at ad (tile usage policy); a Django alapértéke, a "same-origin", nem küld Referert más domainre.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# HTTPS és sütik: csak éles módban (DEBUG=0); fejlesztésnél sima http://127.0.0.1 is működjön.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = False if DEBUG else env_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = 0 if DEBUG else int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))
# Csak proxy/alagút mögött kapcsold be: proxy nélkül a kliens hamisíthatja az X-Forwarded-Proto fejlécet.
# Proxy mögött viszont kell, különben SECURE_SSL_REDIRECT=1 mellett végtelen átirányítás lesz.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if env_bool("TRUST_PROXY_SSL_HEADER", False) else None

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

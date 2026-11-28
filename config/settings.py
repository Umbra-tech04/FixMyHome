import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

from django.core.exceptions import ImproperlyConfigured

from config.security import env_bool, env_choice, env_int, validate_secret_key

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
    "axes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Az utolsó legyen: a tiltási választ ez rendereli (django-axes).
    "axes.middleware.AxesMiddleware",
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
        "OPTIONS": {"user_attributes": ("email", "name", "phone")},
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
SECURE_HSTS_SECONDS = 0 if DEBUG else env_int("SECURE_HSTS_SECONDS", 3600, min_value=0)
# Csak proxy/alagút mögött kapcsold be: proxy nélkül a kliens hamisíthatja az X-Forwarded-Proto fejlécet.
# Proxy mögött viszont kell, különben SECURE_SSL_REDIRECT=1 mellett végtelen átirányítás lesz.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if env_bool("TRUST_PROXY_SSL_HEADER", False) else None

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

# Jelszótippelés elleni védelem (django-axes): a /belepes/ és az /admin/ belépést is védi.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # az első legyen
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = env_int("AXES_FAILURE_LIMIT", 5, min_value=1)
AXES_COOLOFF_TIME = timedelta(minutes=env_int("AXES_COOLOFF_MINUTES", 15, min_value=1))
AXES_RESET_ON_SUCCESS = True
# Csak e-mail szerint tiltunk: alagút mögött mindenki ugyanarról az IP-ről jön.
# Az IP-t az axes a REMOTE_ADDR-ből veszi; az X-Forwarded-For fejlécet (hamisítható) nem használja.
AXES_LOCKOUT_PARAMETERS = ["username"]
# A login űrlapok (saját és admin) mezője "username"; az axes alapértéke a USERNAME_FIELD ("email") lenne,
# amivel minden próba üres felhasználónévvel, egy közös számlálón kötne ki.
AXES_USERNAME_FORM_FIELD = "username"
AXES_USERNAME_CALLABLE = "accounts.throttling.normalize_username"
AXES_LOCKOUT_CALLABLE = "accounts.throttling.lockout_response"
# A sikeres belépéseket nem naplózzuk (kevesebb személyes adat); a sikertelen próbák így is számítanak.
AXES_DISABLE_ACCESS_LOG = True
# Az axes.W006 IP szerinti tiltást javasol. Alagút mögött minden kérés REMOTE_ADDR-e 127.0.0.1,
# így az IP szerinti tiltás egyszerre zárna ki mindenkit; ezért szándékosan csak e-mail szerint tiltunk.
SILENCED_SYSTEM_CHECKS = ["axes.W006"]

# Levélküldés. Fejlesztésben "console": a levelet (a megerősítő linkkel együtt) a terminál írja ki.
# Élesben "smtp"; a jelszó csak a .env-ben (vagy a környezetben) lehet, sosem a repóban.
EMAIL_BACKENDS = {
    "console": "django.core.mail.backends.console.EmailBackend",
    "smtp": "django.core.mail.backends.smtp.EmailBackend",
}
EMAIL_BACKEND = EMAIL_BACKENDS[env_choice("EMAIL_BACKEND", "console", tuple(EMAIL_BACKENDS))]
EMAIL_HOST = os.environ.get("EMAIL_HOST", "").strip()
EMAIL_PORT = env_int("EMAIL_PORT", 587, min_value=1, max_value=65535)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
# A Django alapból korlát nélkül várna egy lassú SMTP-szerverre; így a kérés legfeljebb ennyit vár.
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10, min_value=1)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "").strip() or "MesterKereső <noreply@localhost>"
if EMAIL_BACKEND == EMAIL_BACKENDS["smtp"] and not EMAIL_HOST:
    raise ImproperlyConfigured("EMAIL_BACKEND=smtp mellett az EMAIL_HOST megadása kötelező.")

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

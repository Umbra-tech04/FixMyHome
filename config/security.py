"""Small, settings-independent helpers for production safety checks."""

import os

from django.core.exceptions import ImproperlyConfigured

MIN_SECRET_KEY_LENGTH = 50

# Keys that are public (committed to the repo), so they must never be used with DEBUG off.
DEV_SECRET_KEYS = frozenset({
    "csak-fejlesztesi-kulcs",  # .env.example
    "dev-only-insecure-key-change-me",  # settings.py fallback in DEBUG mode
})


def env_bool(name: str, default: bool) -> bool:
    """Read a "1"/"0" environment flag; anything else is a configuration error."""
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    if value not in ("0", "1"):
        raise ImproperlyConfigured(f"A(z) {name} értéke csak 1 vagy 0 lehet.")
    return value == "1"


def validate_secret_key(key: str, debug: bool) -> None:
    """Raise ImproperlyConfigured if DEBUG is off and the key is missing or weak.

    The message never contains the key itself.
    """
    if debug:
        return
    if not key:
        raise ImproperlyConfigured("A SECRET_KEY környezeti változó kötelező, ha a DEBUG ki van kapcsolva.")
    if key in DEV_SECRET_KEYS:
        raise ImproperlyConfigured("A SECRET_KEY egy nyilvános fejlesztési kulcs; élesben generálj egyedit.")
    if key.startswith("django-insecure"):
        raise ImproperlyConfigured("A SECRET_KEY 'django-insecure' előtagú; élesben generálj egyedit.")
    if len(key) < MIN_SECRET_KEY_LENGTH:
        raise ImproperlyConfigured(
            f"A SECRET_KEY legalább {MIN_SECRET_KEY_LENGTH} karakter legyen, ha a DEBUG ki van kapcsolva."
        )

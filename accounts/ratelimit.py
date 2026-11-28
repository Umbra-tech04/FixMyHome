"""Per-address limits on account e-mails, kept in Django's cache.

The cache key holds a hash of the address, not the address itself. With the default LocMemCache every
server process counts on its own (and a restart forgets), so with N processes the real limit is up to N times
higher. These limits protect inboxes from floods; they are not a security boundary. A shared cache
(Redis, Memcached or DatabaseCache in CACHES) makes them exact.
"""

import hashlib

from django.core.cache import cache

MINUTE = 60
HOUR = 60 * 60


def _key(kind: str, email: str) -> str:
    digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    return f"accounts:{kind}:{digest}"


VERIFICATION_EMAILS_PER_HOUR = 5
PASSWORD_RESET_EMAILS_PER_HOUR = 5


def _allow_minute_and_hour(kind: str, email: str, per_hour: int) -> bool:
    """At most one e-mail of this kind per address per minute and per_hour per hour.

    The hour is a fixed window that starts with the first e-mail, not a sliding one.
    """
    if not cache.add(_key(f"{kind}-minute", email), True, timeout=MINUTE):
        return False
    hour_key = _key(f"{kind}-hour", email)
    cache.add(hour_key, 0, timeout=HOUR)
    try:
        sent = cache.incr(hour_key)
    except ValueError:  # the window expired between add() and incr()
        cache.set(hour_key, 1, timeout=HOUR)
        sent = 1
    return sent <= per_hour


def allow_verification_email(email: str) -> bool:
    """At most one verification e-mail per address per minute and five per hour (registration included)."""
    return _allow_minute_and_hour("verification", email, VERIFICATION_EMAILS_PER_HOUR)


def allow_password_reset_email(email: str) -> bool:
    """At most one password reset e-mail per address per minute and five per hour, counted on its own."""
    return _allow_minute_and_hour("password-reset", email, PASSWORD_RESET_EMAILS_PER_HOUR)


def allow_already_registered_email(email: str) -> bool:
    """At most one "you already have an account" e-mail per address per hour."""
    # cache.add only writes when the key is missing, so it is the check and the claim in one step.
    return cache.add(_key("already-registered", email), True, timeout=HOUR)

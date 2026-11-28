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


def allow_already_registered_email(email: str) -> bool:
    """At most one "you already have an account" e-mail per address per hour."""
    # cache.add only writes when the key is missing, so it is the check and the claim in one step.
    return cache.add(_key("already-registered", email), True, timeout=HOUR)

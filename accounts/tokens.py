"""Signed, expiring e-mail verification tokens (django.core.signing, no database table).

The payload holds the user's id and a SHA-256 hash of the e-mail address, so a token stops working when the
address changes. Signing does not encrypt, and the token ends up in URLs and access logs; the hash keeps the
address itself out of them.
The salt keeps these tokens apart from every other signed value made with the same SECRET_KEY.
Using a token twice is harmless: verifying an already verified account changes nothing.
"""

import hashlib
import hmac
from datetime import timedelta

from django.core import signing

from accounts.models import User

VERIFICATION_SALT = "accounts.email-verification"
VERIFICATION_MAX_AGE = timedelta(hours=24)


def email_hash(email: str) -> str:
    """SHA-256 (hex) of the trimmed, lowercased address."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def make_verification_token(user: User) -> str:
    return signing.dumps({"uid": user.pk, "email_hash": email_hash(user.email)}, salt=VERIFICATION_SALT)


def user_from_verification_token(token: str) -> User | None:
    """The token's user, or None if the token is forged, expired, malformed or no longer matches the account."""
    try:
        payload = signing.loads(token, salt=VERIFICATION_SALT, max_age=VERIFICATION_MAX_AGE)
    except signing.BadSignature:  # SignatureExpired is a subclass
        return None
    if not isinstance(payload, dict):
        return None
    uid, expected_hash = payload.get("uid"), payload.get("email_hash")
    if not isinstance(uid, int) or not isinstance(expected_hash, str):
        return None
    user = User.objects.filter(pk=uid).first()
    if user is None or not hmac.compare_digest(email_hash(user.email), expected_hash):
        return None
    return user

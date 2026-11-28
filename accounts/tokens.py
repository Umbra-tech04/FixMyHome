"""Signed, expiring e-mail verification tokens (django.core.signing, no database table).

The payload holds the user's id and e-mail address, so a token stops working when the address changes.
The salt keeps these tokens apart from every other signed value made with the same SECRET_KEY.
Using a token twice is harmless: verifying an already verified account changes nothing.
"""

from datetime import timedelta

from django.core import signing

from accounts.models import User

VERIFICATION_SALT = "accounts.email-verification"
VERIFICATION_MAX_AGE = timedelta(hours=24)


def make_verification_token(user: User) -> str:
    return signing.dumps({"uid": user.pk, "email": user.email}, salt=VERIFICATION_SALT)


def user_from_verification_token(token: str) -> User | None:
    """The token's user, or None if the token is forged, expired, malformed or no longer matches the account."""
    try:
        payload = signing.loads(token, salt=VERIFICATION_SALT, max_age=VERIFICATION_MAX_AGE)
    except signing.BadSignature:  # SignatureExpired is a subclass
        return None
    if not isinstance(payload, dict):
        return None
    uid, email = payload.get("uid"), payload.get("email")
    if not isinstance(uid, int) or not isinstance(email, str):
        return None
    return User.objects.filter(pk=uid, email=email).first()

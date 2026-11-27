"""Shared validators for user data: used by the registration form AND the User model (so the admin checks the same)."""

import re
import unicodedata

import phonenumbers
from disposable_email_domains import blocklist as DISPOSABLE_DOMAINS
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible

EMAIL_MAX_LENGTH = 254
NAME_MIN_LENGTH, NAME_MAX_LENGTH = 2, 150
PHONE_DEFAULT_REGION = "RS"
PHONE_MAX_LENGTH = 30

# Small, local additions to the disposable-email-domains package list (add new ones here).
EXTRA_DISPOSABLE_DOMAINS = frozenset({
    "tempmail.com",
})

# Characters a typed phone number may contain. Letters are rejected up front, because phonenumbers
# would otherwise read them as keypad digits ("abc" -> "222") and accept the number.
PHONE_CHARS = re.compile(r"^\+?[\d\s()/.-]+$")
NAME_PUNCTUATION = frozenset(" -'’.")


@deconstructible
class StrictEmailValidator(EmailValidator):
    """Django's EmailValidator, but no "localhost" and no IP-literal domains: the domain needs a dot and a TLD."""

    message = "Érvényes e-mail-címet adj meg (pl. nev@pelda.hu)."

    def __init__(self):
        super().__init__(message=self.message, allowlist=[])

    def validate_domain_part(self, domain_part):
        return bool(self.domain_regex.match(domain_part))


_strict_email = StrictEmailValidator()


def is_disposable_domain(domain: str) -> bool:
    """True for a listed domain or any of its subdomains (x.mailinator.com)."""
    parts = domain.lower().split(".")
    candidates = {".".join(parts[i:]) for i in range(len(parts) - 1)}
    return any(c in DISPOSABLE_DOMAINS or c in EXTRA_DISPOSABLE_DOMAINS for c in candidates)


def validate_email_address(value: str) -> None:
    email = value.strip().lower()
    if len(email) > EMAIL_MAX_LENGTH:
        raise ValidationError(f"Az e-mail-cím legfeljebb {EMAIL_MAX_LENGTH} karakter lehet.", code="max_length")
    _strict_email(email)
    if is_disposable_domain(email.rpartition("@")[2]):
        raise ValidationError("Eldobható e-mail-cím nem használható, adj meg egy állandó címet.", code="disposable")


def _parse_phone(value: str) -> phonenumbers.PhoneNumber:
    error = ValidationError("Érvényes telefonszámot adj meg, pl. +381 64 123 4567.", code="invalid_phone")
    raw = value.strip()
    if len(raw) > PHONE_MAX_LENGTH or not PHONE_CHARS.match(raw):
        raise error
    try:
        number = phonenumbers.parse(raw, PHONE_DEFAULT_REGION)
    except phonenumbers.NumberParseException:
        raise error from None
    if not phonenumbers.is_valid_number(number):
        raise error
    return number


def validate_phone(value: str) -> None:
    _parse_phone(value)


def normalize_phone(value: str) -> str:
    """E.164, e.g. "064/123-4567" -> "+381641234567". Raises ValidationError for invalid numbers."""
    return phonenumbers.format_number(_parse_phone(value), phonenumbers.PhoneNumberFormat.E164)


def normalize_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def validate_name(value: str) -> None:
    name = normalize_name(value)
    error = ValidationError(
        "Add meg a teljes neved: 2–150 karakter, csak betűk, szóköz, kötőjel, aposztróf és pont.",
        code="invalid_name",
    )
    if not NAME_MIN_LENGTH <= len(name) <= NAME_MAX_LENGTH:
        raise error
    letters = 0
    for char in name:
        if char.isalpha():
            letters += 1
        elif char not in NAME_PUNCTUATION and unicodedata.category(char) != "Mn":
            raise error
    if letters < NAME_MIN_LENGTH:
        raise error


def validate_no_angle_brackets(value: str) -> None:
    if "<" in value or ">" in value:
        raise ValidationError("A < és > jel nem használható.", code="angle_brackets")

"""Account e-mails: plain text, Hungarian, rendered from templates/accounts/email/."""

import logging
import smtplib

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User
from accounts.ratelimit import allow_already_registered_email, allow_password_reset_email, allow_verification_email
from accounts.tokens import make_verification_token

logger = logging.getLogger(__name__)


def _render(request, template: str, user: User, **context) -> tuple[str, str]:
    """The (subject, body) of one e-mail."""
    context.update(
        user=user, login_url=request.build_absolute_uri(reverse("login")), site_name=settings.SITE_NAME,
    )
    subject = " ".join(render_to_string(f"accounts/email/{template}_subject.txt", context).split())
    body = render_to_string(f"accounts/email/{template}_body.txt", context)
    return subject, body


def _send(request, template: str, user: User, **context) -> None:
    _deliver(template, user, *_render(request, template, user, **context))


def _deliver(template: str, user: User, subject: str, body: str) -> None:
    """Send one e-mail; a delivery failure is logged (without address or token) instead of breaking the page."""
    try:
        send_mail(subject, body, None, [user.email])
    except (smtplib.SMTPException, OSError, UnicodeError) as error:
        # Same response either way: the user can ask for a new e-mail on the resend page.
        # UnicodeError: the console backend on a non-UTF-8 stdout (Windows; fix with PYTHONUTF8=1).
        # Only the exception type is logged: e.g. SMTPRecipientsRefused would print the address.
        logger.error("Could not send the %s e-mail (user id %s): %s", template, user.pk, type(error).__name__)


def send_verification_email(request, user: User) -> None:
    """Send a fresh verification link, unless this address hit the resend limit (accounts.ratelimit)."""
    if not allow_verification_email(user.email):
        return
    # build_absolute_uri uses the Host header, which ALLOWED_HOSTS has already checked.
    verify_url = request.build_absolute_uri(reverse("verify_email", args=[make_verification_token(user)]))
    _send(request, "verification", user, verify_url=verify_url)


def send_existing_account_notice(request, user: User) -> None:
    """Someone registered with an address that already has an account (K3): tell the owner, nobody else.

    A still unverified owner gets a new verification e-mail instead, since "log in" would not work for them.
    """
    if not user.is_active:
        return
    if not user.email_verified:
        send_verification_email(request, user)
    elif allow_already_registered_email(user.email):
        password_reset_url = request.build_absolute_uri(reverse("password_reset"))
        _send(request, "already_registered", user, password_reset_url=password_reset_url)


def password_reset_recipient(email: str) -> User | None:
    """The account that may get a reset e-mail for this address, or None.

    Inactive accounts get none, and neither do superusers: they change their password with
    "manage.py changepassword", so a taken-over mailbox cannot hand out full admin rights.
    Unusable passwords are skipped, as Django's own PasswordResetForm does.
    """
    user = User.objects.filter(email__iexact=email.strip(), is_active=True, is_superuser=False).first()
    if user is None or not user.has_usable_password():
        return None
    return user


def send_password_reset_email(request, email: str) -> None:
    """Send a reset link to the account of this address, if there is one that may get it (K3: silent otherwise).

    Timing: the e-mail is built for every address, so only the delivery itself differs between the branches.
    """
    user = password_reset_recipient(email)
    # Only real recipients touch the rate limit cache, so random addresses cannot push real counters out of it.
    deliver = user is not None and allow_password_reset_email(user.email)
    target = user if user is not None else User(email=email, password="!")  # unsaved stand-in, never sent
    uid = urlsafe_base64_encode(force_bytes(target.pk))
    token = default_token_generator.make_token(target)
    reset_url = request.build_absolute_uri(reverse("password_reset_confirm", args=[uid, token]))
    subject, body = _render(request, "password_reset", target, reset_url=reset_url)
    if deliver:
        _deliver("password_reset", user, subject, body)

"""Account e-mails: plain text, Hungarian, rendered from templates/accounts/email/."""

import logging
import smtplib

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from accounts.models import User
from accounts.ratelimit import allow_already_registered_email
from accounts.tokens import make_verification_token

logger = logging.getLogger(__name__)


def _send(request, template: str, user: User, **context) -> None:
    """Send one e-mail; a delivery failure is logged (without address or token) instead of breaking the page."""
    context.update(user=user, login_url=request.build_absolute_uri(reverse("login")))
    subject = " ".join(render_to_string(f"accounts/email/{template}_subject.txt", context).split())
    body = render_to_string(f"accounts/email/{template}_body.txt", context)
    try:
        send_mail(subject, body, None, [user.email])
    except (smtplib.SMTPException, OSError) as error:
        # Same response either way: the user can ask for a new e-mail on the resend page.
        # Only the exception type is logged: e.g. SMTPRecipientsRefused would print the address.
        logger.error("Could not send the %s e-mail (user id %s): %s", template, user.pk, type(error).__name__)


def send_verification_email(request, user: User) -> None:
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
        # There is no "forgotten password" page yet (7b), so that line links to the login page as well.
        _send(request, "already_registered", user, password_reset_url=request.build_absolute_uri(reverse("login")))

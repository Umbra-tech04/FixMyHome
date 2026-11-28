from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render

from accounts.emails import send_existing_account_notice, send_verification_email
from accounts.forms import RegistrationForm, ResendVerificationForm
from accounts.models import MasterProfile, User
from accounts.tokens import user_from_verification_token

VERIFIED_MESSAGE = "Az e-mail-címedet megerősítettük, most már beléphetsz."


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user, created = form.save()
        # K3: both branches end in the same redirect, with no message or cookie, so the response does not
        # reveal whether the address already had an account. No login: the e-mailed link comes first.
        if created:
            send_verification_email(request, user)
        else:
            send_existing_account_notice(request, user)
        return redirect("verification_sent")
    return render(request, "accounts/register.html", {"form": form})


def verification_sent(request):
    return render(request, "accounts/verification_sent.html")


def resend_verification(request):
    """Ask for a new verification e-mail. The answer never tells whether such an account exists."""
    form = ResendVerificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.filter(
            email__iexact=form.cleaned_data["email"], is_active=True, email_verified=False,
        ).first()
        if user is not None:
            send_verification_email(request, user)  # rate limited per address
        return redirect("resend_verification_sent")
    return render(request, "accounts/verification_resend.html", {"form": form})


def resend_verification_sent(request):
    return render(request, "accounts/verification_resend_sent.html")


def verify_email(request, token):
    """Confirm the address from the e-mailed link. It never logs in, so the link is not a login key."""
    user = user_from_verification_token(token)
    if user is None or not user.is_active:
        return render(request, "accounts/verification_invalid.html", status=400)
    with transaction.atomic():
        # Only the first use changes anything, so a reused link cannot undo a master's later "unavailable" choice.
        if User.objects.filter(pk=user.pk, email_verified=False).update(email_verified=True):
            # Unverified masters are hidden from the search (is_available=False since registration).
            MasterProfile.objects.filter(user=user).update(is_available=True)
    messages.success(request, VERIFIED_MESSAGE)
    # The redirect also drops the token from the address bar.
    return redirect("login")

from axes.utils import reset as reset_axes_attempts
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from accounts.emails import send_existing_account_notice, send_password_reset_email, send_verification_email
from accounts.forms import EmailAddressForm, NewPasswordForm, RegistrationForm
from accounts.models import User, mark_email_verified
from accounts.tokens import user_from_verification_token

VERIFIED_MESSAGE = "Az e-mail-címedet megerősítettük, most már beléphetsz."
PASSWORD_CHANGED_MESSAGE = "Jelszavad megváltozott, most már beléphetsz az új jelszóval."


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
    form = EmailAddressForm(request.POST or None)
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
    mark_email_verified([user.pk])  # a reused link changes nothing
    messages.success(request, VERIFIED_MESSAGE)
    # The redirect also drops the token from the address bar.
    return redirect("login")


def password_reset(request):
    """Ask for a password reset e-mail. The answer is the same whether or not an e-mail goes out (K3)."""
    form = EmailAddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        send_password_reset_email(request, form.cleaned_data["email"])  # silent for unknown addresses; rate limited
        return redirect("password_reset_sent")
    return render(request, "accounts/password_reset.html", {"form": form})


def password_reset_sent(request):
    return render(request, "accounts/password_reset_sent.html")


class PasswordResetConfirm(PasswordResetConfirmView):
    """Django's view: the e-mailed link puts the token in the session and redirects to a fixed address
    (".../uj-jelszo/"), so the token does not stay in the address bar, the Referer header or later log lines.
    """

    reset_url_token = "uj-jelszo"
    template_name = "accounts/password_reset_confirm.html"
    form_class = NewPasswordForm
    success_url = reverse_lazy("login")

    def get_user(self, uidb64):
        # The same accounts as in accounts.emails.password_reset_recipient: Django would also accept one that
        # was deactivated, or made a superuser, after the e-mail went out.
        user = super().get_user(uidb64)
        return user if user is not None and user.is_active and not user.is_superuser else None

    def form_valid(self, form):
        # Saves the password and drops the token from the session. Every existing session of the account ends:
        # Django keeps a hash of the password in each session, and it no longer matches (so no
        # update_session_auth_hash here). There is no login(): the user logs in with the new password.
        response = super().form_valid(form)
        user = form.user
        if self.request.user.is_authenticated:
            logout(self.request)  # whoever is logged in on this browser
        # The e-mailed link proves the mailbox is theirs; this also shows an unverified master in the search.
        mark_email_verified([user.pk])
        # Lift this address's login lockout (axes keys attempts by the lowercased address).
        reset_axes_attempts(username=user.email)
        messages.success(self.request, PASSWORD_CHANGED_MESSAGE)
        return response

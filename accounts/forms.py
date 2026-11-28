from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import password_validators_help_text_html, validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.html import format_html

from accounts.models import MasterProfile, Role, User
from accounts.validators import (
    normalize_name,
    normalize_phone,
    validate_email_address,
    validate_name,
    validate_no_angle_brackets,
    validate_phone,
)
from listings.models import Category

REGISTRATION_ROLES = [(Role.USER.value, Role.USER.label), (Role.MASTER.value, Role.MASTER.label)]
MASTER_ONLY_FIELDS = ("profession", "service_area", "contact")


class RegistrationForm(forms.Form):
    name = forms.CharField(label="Név", max_length=150, validators=[validate_name])
    email = forms.EmailField(label="E-mail", max_length=254, validators=[validate_email_address])
    phone = forms.CharField(label="Telefon", max_length=30, validators=[validate_phone])
    password1 = forms.CharField(label="Jelszó", widget=forms.PasswordInput, help_text=password_validators_help_text_html())
    password2 = forms.CharField(label="Jelszó újra", widget=forms.PasswordInput)
    # Preselected "user", so the master-only fields stay hidden until "Mester vagyok" is picked; still required.
    role = forms.ChoiceField(label="Szerepkör", choices=REGISTRATION_ROLES, initial=Role.USER.value)
    profession = forms.ModelChoiceField(label="Szakma (csak mestereknek)", queryset=Category.objects.all(), required=False)
    # TEMPORARY: PR 3b (registration form redesign) replaces the master-only fields; until then only
    # trimming (CharField default), the length limit and the < > ban apply.
    service_area = forms.CharField(
        label="Működési terület (csak mestereknek)", max_length=200, required=False,
        validators=[validate_no_angle_brackets],
    )
    contact = forms.CharField(
        label="Elérhetőség (csak mestereknek)", max_length=200, required=False,
        validators=[validate_no_angle_brackets],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in MASTER_ONLY_FIELDS:
            self.fields[name].widget.attrs["data-master-only"] = "1"
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["name"].widget.attrs["autocomplete"] = "name"

    def clean_name(self):
        return normalize_name(self.cleaned_data["name"])

    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"])

    def clean_email(self):
        # No "already registered" error here (K3): it would tell anyone which addresses have an account.
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "A két jelszó nem egyezik.")
        elif password1:
            try:
                # Unsaved user, so the similarity check can compare against e-mail, name and phone.
                candidate = User(
                    email=cleaned.get("email", ""), name=cleaned.get("name", ""), phone=cleaned.get("phone", ""),
                )
                validate_password(password1, user=candidate)
            except ValidationError as error:
                self.add_error("password1", error)
        is_master = cleaned.get("role") == Role.MASTER
        for field in MASTER_ONLY_FIELDS:
            if is_master and not cleaned.get(field):
                self.add_error(field, "Mestereknél ez a mező kötelező.")
            elif cleaned.get("role") == Role.USER and cleaned.get(field):
                self.add_error(field, "Ez a mező csak mester szerepkörnél adható meg.")
        return cleaned

    def save(self) -> tuple[User, bool]:
        """Create the account, or return the existing one for this address: (user, created).

        The caller must answer both cases identically (K3). A parallel registration that wins the race for the
        same address (IntegrityError) takes the existing-account branch too.
        """
        email = self.cleaned_data["email"]
        existing = self._find_existing(email)
        if existing is not None:
            # Hash anyway, so this branch costs about as much time as creating an account.
            make_password(self.cleaned_data["password1"])
            return existing, False
        try:
            return self._create(), True
        except IntegrityError:
            existing = User.objects.filter(email__iexact=email).first()
            if existing is None:
                raise  # not the e-mail race: a real bug, let it surface
            return existing, False

    @staticmethod
    def _find_existing(email: str) -> User | None:
        return User.objects.filter(email__iexact=email).first()

    @transaction.atomic
    def _create(self) -> User:
        data = self.cleaned_data
        user = User.objects.create_user(
            email=data["email"], password=data["password1"],
            name=data["name"], phone=data["phone"], role=data["role"],
            email_verified=False,  # the model default is True; only self-registration needs confirmation
        )
        if data["role"] == Role.MASTER:
            MasterProfile.objects.create(
                user=user, profession=data["profession"],
                service_area=data["service_area"], contact=data["contact"],
                is_available=False,  # hidden from the search until the e-mail is verified (accounts.views.verify_email)
            )
        return user


UNVERIFIED_LOGIN_MESSAGE = (
    "Még nem erősítetted meg az e-mail-címedet. Nyisd meg a levelünkben kapott linket, "
    'vagy <a href="{url}">kérj új levelet</a>.'
)


def ensure_email_verified(user: User) -> None:
    # Runs only after authenticate() accepted the password, so axes does not count it as a failed attempt,
    # and only someone who knows the password learns that the account exists.
    if not user.email_verified:
        # format_html gives a safe string, so the login templates ({{ error }}) show a real link.
        # It contains no user input; the URL is fixed (no "next" parameter, so no open redirect).
        message = format_html(UNVERIFIED_LOGIN_MESSAGE, url=reverse("resend_verification"))
        raise ValidationError(message, code="email_unverified")


class EmailAddressForm(forms.Form):
    """One e-mail field: the verification resend and the password reset request pages."""

    email = forms.EmailField(label="E-mail", max_length=254)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["autocomplete"] = "email"

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class EmailAuthenticationForm(AuthenticationForm):
    """Site login: an unverified account cannot log in, even with the right password."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        ensure_email_verified(user)


class AdminEmailAuthenticationForm(AdminAuthenticationForm):
    """/admin/ login: the staff check first, then the same e-mail check as on the site."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        ensure_email_verified(user)


class NewPasswordForm(SetPasswordForm):
    """The password reset's new password: Django's form, which runs AUTH_PASSWORD_VALIDATORS against the
    real account (so it cannot resemble its e-mail, name or phone), with the registration's wording.
    """

    error_messages = {**SetPasswordForm.error_messages, "password_mismatch": "A két jelszó nem egyezik."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Új jelszó"
        self.fields["new_password2"].label = "Új jelszó újra"

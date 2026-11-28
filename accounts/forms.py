from django import forms
from django.contrib.auth.password_validation import password_validators_help_text_html, validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

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
DUPLICATE_EMAIL_MESSAGE = "Ezzel az e-mail-címmel már van fiók."
MASTER_ONLY_FIELDS = ("profession", "service_area", "contact")


class RegistrationForm(forms.Form):
    name = forms.CharField(label="Név", max_length=150, validators=[validate_name])
    email = forms.EmailField(label="E-mail", max_length=254, validators=[validate_email_address])
    phone = forms.CharField(label="Telefon", max_length=30, validators=[validate_phone])
    password1 = forms.CharField(label="Jelszó", widget=forms.PasswordInput, help_text=password_validators_help_text_html())
    password2 = forms.CharField(label="Jelszó újra", widget=forms.PasswordInput)
    role = forms.ChoiceField(label="Szerepkör", choices=REGISTRATION_ROLES)
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
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(DUPLICATE_EMAIL_MESSAGE)
        return email

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

    def save(self) -> User | None:
        """Create the account. Returns None (with an e-mail form error) if a parallel request took the address."""
        try:
            return self._create()
        except IntegrityError:
            if not User.objects.filter(email__iexact=self.cleaned_data["email"]).exists():
                raise  # not the e-mail race: a real bug, let it surface
            self.add_error("email", DUPLICATE_EMAIL_MESSAGE)
            return None

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

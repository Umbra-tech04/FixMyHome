import re

from django import forms
from django.contrib.auth.password_validation import password_validators_help_text_html, validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import MasterProfile, Role, User
from listings.models import Category

REGISTRATION_ROLES = [(Role.USER.value, Role.USER.label), (Role.MASTER.value, Role.MASTER.label)]
MASTER_ONLY_FIELDS = ("profession", "service_area", "contact")
PHONE_PATTERN = re.compile(r"^\+?[\d\s()/.-]+$")


class RegistrationForm(forms.Form):
    name = forms.CharField(label="Név", max_length=150)
    email = forms.EmailField(label="E-mail", max_length=254)
    phone = forms.CharField(label="Telefon", max_length=30)
    password1 = forms.CharField(label="Jelszó", widget=forms.PasswordInput, help_text=password_validators_help_text_html())
    password2 = forms.CharField(label="Jelszó újra", widget=forms.PasswordInput)
    role = forms.ChoiceField(label="Szerepkör", choices=REGISTRATION_ROLES)
    profession = forms.ModelChoiceField(label="Szakma (csak mestereknek)", queryset=Category.objects.all(), required=False)
    service_area = forms.CharField(label="Működési terület (csak mestereknek)", max_length=200, required=False)
    contact = forms.CharField(label="Elérhetőség (csak mestereknek)", max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in MASTER_ONLY_FIELDS:
            self.fields[name].widget.attrs["data-master-only"] = "1"
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["name"].widget.attrs["autocomplete"] = "name"

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2 or not any(char.isalpha() for char in name):
            raise ValidationError("Add meg a teljes neved.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        digits = re.sub(r"\D", "", phone)
        if not PHONE_PATTERN.match(phone) or not 6 <= len(digits) <= 15:
            raise ValidationError("Érvényes telefonszámot adj meg, pl. +381 60 123 4567.")
        return phone

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ezzel az e-mail-címmel már van fiók.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "A két jelszó nem egyezik.")
        elif password1:
            try:
                validate_password(password1)
            except ValidationError as error:
                self.add_error("password1", error)
        is_master = cleaned.get("role") == Role.MASTER
        for field in MASTER_ONLY_FIELDS:
            if is_master and not cleaned.get(field):
                self.add_error(field, "Mestereknél ez a mező kötelező.")
            elif cleaned.get("role") == Role.USER and cleaned.get(field):
                self.add_error(field, "Ez a mező csak mester szerepkörnél adható meg.")
        return cleaned

    @transaction.atomic
    def save(self) -> User:
        data = self.cleaned_data
        user = User.objects.create_user(
            email=data["email"], password=data["password1"],
            name=data["name"], phone=data["phone"], role=data["role"],
        )
        if data["role"] == Role.MASTER:
            MasterProfile.objects.create(
                user=user, profession=data["profession"],
                service_area=data["service_area"], contact=data["contact"],
            )
        return user

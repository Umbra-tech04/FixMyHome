from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import Role, User
from accounts.validators import (
    normalize_name,
    normalize_phone,
    validate_email_address,
    validate_name,
    validate_no_angle_brackets,
    validate_phone,
)

PASSWORD = "Jelszo-12345"


class EmailValidatorTests(SimpleTestCase):
    def test_accepts_normal_addresses(self):
        for email in ("anna@example.com", "kovacs.janos@x.hu", "a+b@sub.domain.rs", "eva@gmail.com"):
            with self.subTest(email=email):
                validate_email_address(email)

    def test_rejects_addresses_without_dotted_domain(self):
        for email in ("valaki@localhost", "valaki@intranet", "a@[127.0.0.1]", "a@[IPv6:::1]", "nincs-kukac.hu", "a@.hu"):
            with self.subTest(email=email), self.assertRaises(ValidationError):
                validate_email_address(email)

    def test_rejects_disposable_providers(self):
        for email in (
            "x@mailinator.com", "x@10minutemail.com", "x@guerrillamail.com", "x@tempmail.com",
            "x@temp-mail.org", "x@yopmail.com", "x@sub.mailinator.com", "x@MAILINATOR.COM",
        ):
            with self.subTest(email=email):
                with self.assertRaisesMessage(ValidationError, "Eldobható e-mail-cím"):
                    validate_email_address(email)

    def test_rejects_overlong_address(self):
        with self.assertRaises(ValidationError):
            validate_email_address("a" * 64 + "@" + "b" * 185 + ".com")  # 254 felett


class PhoneValidatorTests(SimpleTestCase):
    def test_accepts_real_numbers_and_normalizes_to_e164(self):
        cases = {
            "+381 64 123 4567": "+381641234567",
            "064/123-4567": "+381641234567",
            "(021) 456 789": "+38121456789",
            "+36 30 123 4567": "+36301234567",
            "+43 664 1234567": "+436641234567",
            " 060 111 222 ": "+38160111222",
        }
        for raw, e164 in cases.items():
            with self.subTest(phone=raw):
                validate_phone(raw)
                self.assertEqual(normalize_phone(raw), e164)

    def test_rejects_invalid_numbers(self):
        for raw in ("123456", "asdf", "123", "+381 60 abc 123", "1" * 30, "+381", "060 111 222 ext 5"):
            with self.subTest(phone=raw), self.assertRaises(ValidationError):
                validate_phone(raw)


class NameValidatorTests(SimpleTestCase):
    def test_accepts_unicode_names(self):
        for name in ("Kovács Éva", "Đorđe Petrović", "Jean-Luc O'Neil", "Anna Mária Szabó-Tóth", "Dr. Kiss Ödön", "Ðuro", "Łukasz"):
            with self.subTest(name=name):
                validate_name(name)

    def test_rejects_bad_names(self):
        for name in ("A", "A.", "12", "---", "Anna2", "<b>Anna</b>", "anna@x.hu", "Anna; DROP", "Anna_B", "x" * 151):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                validate_name(name)

    def test_normalize_collapses_whitespace(self):
        self.assertEqual(normalize_name("  Kovács \t  Éva  "), "Kovács Éva")

    def test_normalize_composes_accents(self):
        decomposed = "Kovács"  # a + combining acute
        self.assertEqual(normalize_name(decomposed), "Kovács")
        validate_name(normalize_name(decomposed))


class AngleBracketValidatorTests(SimpleTestCase):
    def test_rejects_angle_brackets(self):
        for value in ("<script>", "a > b"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_no_angle_brackets(value)

    def test_accepts_plain_text(self):
        validate_no_angle_brackets("Szabadka és környéke, +381 60 222 333")


class UserModelValidationTests(TestCase):
    """The admin uses full_clean(), so the model fields must carry the same validators."""

    def test_model_rejects_invalid_fields(self):
        user = User(email="valaki@localhost", name="Anna2", phone="123456")
        with self.assertRaises(ValidationError) as ctx:
            user.full_clean(exclude=["password"])
        self.assertEqual(set(ctx.exception.message_dict), {"email", "name", "phone"})

    def test_model_clean_normalizes_name_and_phone(self):
        user = User(email="Anna@Example.com", name="  Kovács   Éva ", phone="064/123-4567")
        user.full_clean(exclude=["password"])
        self.assertEqual((user.email, user.name, user.phone), ("anna@example.com", "Kovács Éva", "+381641234567"))

    def test_blank_phone_is_still_allowed_on_the_model(self):
        User(email="support@example.com", name="Ügyfélszolgálat", phone="").full_clean(exclude=["password"])

    def test_admin_add_user_rejects_invalid_name(self):
        admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        self.client.force_login(admin)
        response = self.client.post(reverse("admin:accounts_user_add"), {
            "email": "uj@example.com", "name": "<b>Hacker</b>", "role": Role.USER,
            "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["adminform"].form.errors.get("name"))
        self.assertFalse(User.objects.filter(email="uj@example.com").exists())

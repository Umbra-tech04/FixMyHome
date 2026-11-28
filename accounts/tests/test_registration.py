from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.forms import RegistrationForm
from accounts.models import MasterProfile, Role, User
from listings.models import Category

PASSWORD = "Jelszo-12345"


def valid_data(**overrides):
    data = {
        "name": "Anna", "email": "anna@example.com", "phone": "+381 60 111 222",
        "password1": PASSWORD, "password2": PASSWORD, "role": Role.USER,
    }
    data.update(overrides)
    return data


def master_data(**overrides):
    data = valid_data(
        email="bela@example.com", name="Béla", role=Role.MASTER,
        profession=Category.objects.get(name="Vízszerelő").pk,
        service_area="Szabadka és környéke", contact="+381 60 222 333",
    )
    data.update(overrides)
    return data


class RegistrationTests(TestCase):
    url = reverse("register")

    def test_user_registration_creates_account(self):
        # Changed with e-mail verification: no automatic login, the "e-mail sent" page follows instead.
        response = self.client.post(self.url, valid_data())
        self.assertRedirects(response, reverse("verification_sent"))
        user = User.objects.get(email="anna@example.com")
        self.assertEqual(user.role, Role.USER)
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_registration_creates_unverified_account(self):
        self.client.post(self.url, valid_data())
        self.assertFalse(User.objects.get(email="anna@example.com").email_verified)

    def test_master_registration_creates_profile(self):
        self.client.post(self.url, master_data())
        user = User.objects.get(email="bela@example.com")
        self.assertEqual(user.role, Role.MASTER)
        profile = user.master_profile
        self.assertEqual(profile.profession.name, "Vízszerelő")
        self.assertEqual(profile.service_area, "Szabadka és környéke")
        self.assertEqual(profile.contact, "+381 60 222 333")

    def test_master_without_profile_data_is_rejected_atomically(self):
        response = self.client.post(self.url, master_data(profession=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("profession", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(MasterProfile.objects.count(), 0)

    # Changed with e-mail verification (K3): an existing address gets the same "e-mail sent" page as a new one,
    # with no error message, so the form does not reveal which addresses have an account.
    def test_duplicate_email_creates_no_account_and_shows_no_error(self):
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        response = self.client.post(self.url, valid_data())
        self.assertRedirects(response, reverse("verification_sent"))
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_email_is_case_insensitive(self):
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        response = self.client.post(self.url, valid_data(email="Anna@Example.com"))
        self.assertRedirects(response, reverse("verification_sent"))
        self.assertEqual(User.objects.count(), 1)

    def test_support_and_company_roles_cannot_be_chosen(self):
        for role in (Role.SUPPORT, Role.COMPANY):
            with self.subTest(role=role):
                response = self.client.post(self.url, valid_data(role=role))
                self.assertEqual(response.status_code, 200)
                self.assertIn("role", response.context["form"].errors)
                self.assertEqual(User.objects.count(), 0)

    def test_password_mismatch_shows_error(self):
        response = self.client.post(self.url, valid_data(password2="Mas-jelszo-123"))
        self.assertContains(response, "A két jelszó nem egyezik.")
        self.assertEqual(User.objects.count(), 0)

    def test_weak_password_is_rejected(self):
        response = self.client.post(self.url, valid_data(password1="12345678", password2="12345678"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("password1", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 0)


class RegistrationLimitsTests(TestCase):
    def test_overlong_email_is_rejected_by_the_form(self):
        long_email = "a" * 250 + "@example.com"
        response = self.client.post(reverse("register"), valid_data(email=long_email))
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 0)


class RegistrationRestrictionTests(TestCase):
    url = reverse("register")

    def test_user_cannot_fill_master_only_fields(self):
        extra = {
            "profession": Category.objects.get(name="Vízszerelő").pk,
            "service_area": "Szabadka",
            "contact": "+381 60 222 333",
        }
        for field, value in extra.items():
            with self.subTest(field=field):
                response = self.client.post(self.url, valid_data(**{field: value}))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(User.objects.count(), 0)

    def test_master_only_fields_are_marked_for_the_browser(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-master-only="1"', count=3)

    def test_phone_must_look_like_a_phone_number(self):
        for bad in ("abc", "123", "+381 60 abc 123", "1" * 30):
            with self.subTest(phone=bad):
                response = self.client.post(self.url, valid_data(phone=bad))
                self.assertEqual(response.status_code, 200)
                self.assertIn("phone", response.context["form"].errors)
                self.assertEqual(User.objects.count(), 0)

    def test_common_phone_formats_are_accepted(self):
        for index, good in enumerate(("+381 60 111 222", "060/111-222", "(021) 456 789", "+36 30 123 4567")):
            with self.subTest(phone=good):
                response = self.client.post(self.url, valid_data(email=f"p{index}@example.com", phone=good))
                self.assertEqual(response.status_code, 302)

    def test_name_needs_letters_and_two_characters(self):
        for bad in ("A", "12", "---"):
            with self.subTest(name=bad):
                response = self.client.post(self.url, valid_data(name=bad))
                self.assertEqual(response.status_code, 200)
                self.assertIn("name", response.context["form"].errors)
        response = self.client.post(self.url, valid_data(name="  Kovács   Éva "))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.get().name, "Kovács Éva")

    def test_password_requirements_are_shown(self):
        from django.contrib.auth.password_validation import password_validators_help_text_html

        response = self.client.get(self.url)
        self.assertContains(response, password_validators_help_text_html(), html=True)


class RegistrationValidationTests(TestCase):
    url = reverse("register")

    def assert_field_error(self, field, **overrides):
        response = self.client.post(self.url, valid_data(**overrides))
        self.assertEqual(response.status_code, 200)
        self.assertIn(field, response.context["form"].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_email_is_trimmed_and_lowercased(self):
        self.client.post(self.url, valid_data(email="  Anna@Example.COM "))
        self.assertTrue(User.objects.filter(email="anna@example.com").exists())

    def test_strict_email_rules_apply(self):
        for email in ("valaki@localhost", "a@[127.0.0.1]", "x@mailinator.com", "x@tempmail.com"):
            with self.subTest(email=email):
                self.assert_field_error("email", email=email)

    def test_disposable_email_message_is_shown(self):
        response = self.client.post(self.url, valid_data(email="x@yopmail.com"))
        self.assertContains(response, "Eldobható e-mail-cím nem használható")

    def test_phone_is_stored_in_e164(self):
        self.client.post(self.url, valid_data(phone="064/123-4567"))
        self.assertEqual(User.objects.get().phone, "+381641234567")

    def test_fake_phone_numbers_are_rejected(self):
        for phone in ("123456", "asdf", "+381 60 abc 123"):
            with self.subTest(phone=phone):
                self.assert_field_error("phone", phone=phone)

    def test_names_with_digits_or_markup_are_rejected(self):
        for name in ("Anna2", "<b>Anna</b>", "anna@x.hu", "A."):
            with self.subTest(name=name):
                self.assert_field_error("name", name=name)

    def test_unicode_name_is_accepted(self):
        response = self.client.post(self.url, valid_data(name="Đorđe O'Neil-Petrović"))
        self.assertEqual(response.status_code, 302)

    def test_master_fields_reject_angle_brackets(self):
        for field in ("service_area", "contact"):
            with self.subTest(field=field):
                response = self.client.post(self.url, master_data(**{field: "<script>x</script>"}))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(User.objects.count(), 0)

    def test_master_fields_are_trimmed(self):
        self.client.post(self.url, master_data(service_area="  Szabadka  ", contact="  +381 60 222 333 "))
        profile = MasterProfile.objects.get()
        self.assertEqual((profile.service_area, profile.contact), ("Szabadka", "+381 60 222 333"))


class PasswordSimilarityTests(TestCase):
    """The similarity check must see the new user's e-mail, name and phone."""

    def password_error_codes(self, **overrides):
        form = RegistrationForm(valid_data(**overrides))
        self.assertFalse(form.is_valid())
        return [error.code for error in form.errors.as_data().get("password1", [])]

    def test_password_similar_to_email_is_rejected(self):
        codes = self.password_error_codes(email="kovacs.janos@x.hu", password1="kovacsjanos", password2="kovacsjanos")
        self.assertIn("password_too_similar", codes)

    def test_password_similar_to_name_is_rejected(self):
        codes = self.password_error_codes(name="Teodor Lazarevic", password1="teodorlazarevic", password2="teodorlazarevic")
        self.assertIn("password_too_similar", codes)

    def test_password_similar_to_phone_is_rejected(self):
        codes = self.password_error_codes(phone="+381641234567", password1="tel381641234567", password2="tel381641234567")
        self.assertIn("password_too_similar", codes)

    def test_unrelated_password_is_accepted(self):
        form = RegistrationForm(valid_data(email="kovacs.janos@x.hu", name="Kovács János"))
        self.assertTrue(form.is_valid(), form.errors)


class DuplicateEmailRaceTests(TestCase):
    """Two registrations with the same e-mail at the same time: the loser takes the existing-address branch, not a 500.

    Changed with e-mail verification (K3): this used to be a form error; now it is the same "e-mail sent" page.
    """

    url = reverse("register")

    def setUp(self):
        cache.clear()

    def skip_precheck(self):
        # As if both requests looked for the address before either was saved.
        return mock.patch.object(RegistrationForm, "_find_existing", return_value=None)

    def test_form_save_turns_integrity_error_into_existing_account(self):
        form = RegistrationForm(valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        winner = User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        with self.skip_precheck():
            self.assertEqual(form.save(), (winner, False))
        self.assertFalse(form.errors)
        self.assertEqual(User.objects.count(), 1)

    def test_view_shows_the_same_sent_page_instead_of_500(self):
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        with self.skip_precheck():
            response = self.client.post(self.url, valid_data())
        self.assertRedirects(response, reverse("verification_sent"))
        self.assertEqual(User.objects.count(), 1)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(
            [m.subject for m in mail.outbox], ["Valaki ezzel a címmel próbált regisztrálni a MesterKeresőn"],
        )

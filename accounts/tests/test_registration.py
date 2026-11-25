from django.test import TestCase
from django.urls import reverse

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
        response = self.client.post(self.url, valid_data())
        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(email="anna@example.com")
        self.assertEqual(user.role, Role.USER)
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

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

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        response = self.client.post(self.url, valid_data())
        self.assertContains(response, "Ezzel az e-mail-címmel már van fiók.")
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_email_is_case_insensitive(self):
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        response = self.client.post(self.url, valid_data(email="Anna@Example.com"))
        self.assertContains(response, "Ezzel az e-mail-címmel már van fiók.")
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
        for index, good in enumerate(("+381 60 111 222", "060/111-222", "(021) 123 456", "+36 30 123 4567")):
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

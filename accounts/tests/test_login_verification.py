from axes.models import AccessAttempt
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.tokens import make_verification_token

PASSWORD = "Jelszo-12345"
UNVERIFIED_MESSAGE = "Még nem erősítetted meg az e-mail-címedet."
INVALID_LOGIN = "Írjon be egy helyes"  # start of Django's own Hungarian invalid_login message


class UnverifiedLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="anna@example.com", password=PASSWORD, name="Anna", email_verified=False,
        )

    def login(self, password=PASSWORD, email="anna@example.com"):
        return self.client.post(reverse("login"), {"username": email, "password": password})

    def test_correct_password_does_not_log_in_unverified_account(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, UNVERIFIED_MESSAGE)

    def test_wrong_password_gets_the_generic_message(self):
        response = self.login(password="rossz-jelszo")
        self.assertNotContains(response, UNVERIFIED_MESSAGE)
        self.assertContains(response, INVALID_LOGIN)

    def test_unverified_attempts_are_not_counted_by_axes(self):
        for _ in range(10):
            self.login()
        self.assertFalse(AccessAttempt.objects.exists())
        self.client.get(reverse("verify_email", args=[make_verification_token(self.user)]))
        response = self.login()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_verified_account_logs_in(self):
        User.objects.filter(pk=self.user.pk).update(email_verified=True)
        self.assertRedirects(self.login(), reverse("home"))


class UnverifiedAdminLoginTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="admin@example.com", password=PASSWORD, name="Admin", is_staff=True, email_verified=False,
        )

    def admin_login(self):
        return self.client.post(
            reverse("admin:login"), {"username": "admin@example.com", "password": PASSWORD, "next": "/admin/"},
        )

    def test_unverified_staff_cannot_log_in_to_admin(self):
        response = self.admin_login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, UNVERIFIED_MESSAGE)
        self.assertFalse(AccessAttempt.objects.exists())

    def test_verified_staff_logs_in_to_admin(self):
        User.objects.filter(pk=self.staff.pk).update(email_verified=True)
        self.assertRedirects(self.admin_login(), "/admin/")

    def test_non_staff_still_gets_the_admin_refusal(self):
        User.objects.filter(pk=self.staff.pk).update(is_staff=False, email_verified=True)
        response = self.admin_login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

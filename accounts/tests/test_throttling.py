from datetime import timedelta

from axes.models import AccessAttempt, AccessLog
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

PASSWORD = "Jelszo-12345"
WRONG = "rossz-jelszo"
LOCKOUT_MESSAGE = "Túl sok sikertelen próbálkozás. Próbáld újra 15 perc múlva."


class LoginThrottlingTests(TestCase):
    def setUp(self):
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        User.objects.create_user(email="bela@example.com", password=PASSWORD, name="Béla")

    def login(self, email, password, **headers):
        return self.client.post(reverse("login"), {"username": email, "password": password}, headers=headers)

    def fail_login(self, email, times):
        for _ in range(times):
            self.login(email, WRONG)

    def assert_logged_in(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
        self.client.logout()

    def assert_locked_out(self, response):
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_four_failures_do_not_lock(self):
        self.fail_login("anna@example.com", 4)
        self.assert_logged_in(self.login("anna@example.com", PASSWORD))

    def test_correct_password_is_blocked_after_five_failures(self):
        self.fail_login("anna@example.com", 5)
        self.assert_locked_out(self.login("anna@example.com", PASSWORD))

    def test_lockout_page_shows_hungarian_message_and_login_link(self):
        self.fail_login("anna@example.com", 5)
        response = self.login("anna@example.com", PASSWORD)
        self.assertContains(response, LOCKOUT_MESSAGE, status_code=429)
        self.assertContains(response, f'href="{reverse("login")}"', status_code=429)
        self.assertTemplateUsed(response, "base.html")

    def test_other_user_is_not_affected(self):
        self.fail_login("anna@example.com", 5)
        self.assert_logged_in(self.login("bela@example.com", PASSWORD))

    def test_lockout_expires_after_cooloff(self):
        self.fail_login("anna@example.com", 5)
        AccessAttempt.objects.update(attempt_time=timezone.now() - timedelta(minutes=16))
        self.assert_logged_in(self.login("anna@example.com", PASSWORD))

    def test_successful_login_resets_failure_count(self):
        self.fail_login("anna@example.com", 4)
        self.assert_logged_in(self.login("anna@example.com", PASSWORD))
        self.fail_login("anna@example.com", 4)
        self.assert_logged_in(self.login("anna@example.com", PASSWORD))

    def test_counter_is_keyed_by_normalized_email(self):
        self.fail_login("Anna@Example.com", 1)
        self.fail_login("bela@example.com", 1)
        self.assertEqual(
            sorted(AccessAttempt.objects.values_list("username", flat=True)),
            ["anna@example.com", "bela@example.com"],
        )

    def test_email_case_variants_share_one_counter(self):
        self.fail_login("Anna@Example.com", 2)
        self.fail_login("ANNA@EXAMPLE.COM", 2)
        self.fail_login(" anna@example.com ", 1)
        self.assert_locked_out(self.login("anna@example.com", PASSWORD))

    def test_unknown_email_is_counted_and_gets_identical_lockout_page(self):
        self.fail_login("nincs@example.com", 5)
        unknown = self.login("nincs@example.com", WRONG)
        self.fail_login("anna@example.com", 5)
        known = self.login("anna@example.com", WRONG)
        self.assertEqual(unknown.status_code, 429)
        self.assertEqual(unknown.content, known.content)

    def test_admin_login_is_protected(self):
        User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        url = reverse("admin:login")
        for _ in range(5):
            self.client.post(url, {"username": "admin@example.com", "password": WRONG})
        response = self.client.post(url, {"username": "admin@example.com", "password": PASSWORD})
        self.assert_locked_out(response)

    def test_spoofed_forwarded_for_header_is_ignored(self):
        self.login("anna@example.com", WRONG, x_forwarded_for="203.0.113.9")
        self.assertEqual(AccessAttempt.objects.get().ip_address, "127.0.0.1")

    def test_successful_logins_are_not_logged(self):
        self.assert_logged_in(self.login("anna@example.com", PASSWORD))
        self.assertFalse(AccessLog.objects.exists())

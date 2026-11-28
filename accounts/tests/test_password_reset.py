import time
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase

from accounts.ratelimit import allow_password_reset_email, allow_verification_email
from config.tests import load_settings


class PasswordResetSettingsTests(SimpleTestCase):
    def test_reset_links_expire_after_one_hour(self):
        self.assertEqual(settings.PASSWORD_RESET_TIMEOUT, 60 * 60)

    def test_site_name_defaults_to_fixmyhome(self):
        self.assertEqual(settings.SITE_NAME, "FixMyHome")

    def test_site_name_can_be_set_in_the_environment(self):
        result = load_settings({"DEBUG": "1", "SITE_NAME": " Proba Oldal "}, expr="s.SITE_NAME")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Proba Oldal")


class PasswordResetRateLimitTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_one_email_a_minute(self):
        now = time.time()
        self.assertTrue(allow_password_reset_email("anna@example.com"))
        self.assertFalse(allow_password_reset_email("anna@example.com"))
        with mock.patch("time.time", return_value=now + 61):
            self.assertTrue(allow_password_reset_email("anna@example.com"))

    def test_five_emails_an_hour(self):
        now = time.time()
        allowed = []
        for minute in range(8):
            with mock.patch("time.time", return_value=now + minute * 61):
                allowed.append(allow_password_reset_email("anna@example.com"))
        self.assertEqual(allowed.count(True), 5)
        with mock.patch("time.time", return_value=now + 60 * 60 + 1):
            self.assertTrue(allow_password_reset_email("anna@example.com"))

    def test_address_is_normalized(self):
        self.assertTrue(allow_password_reset_email("anna@example.com"))
        self.assertFalse(allow_password_reset_email(" ANNA@Example.com "))

    def test_counted_apart_from_verification_emails(self):
        self.assertTrue(allow_verification_email("anna@example.com"))
        self.assertTrue(allow_password_reset_email("anna@example.com"))

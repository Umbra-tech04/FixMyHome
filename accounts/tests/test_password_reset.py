import re
import smtplib
import time
from datetime import datetime, timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User
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


PASSWORD = "Jelszo-12345"
NEUTRAL = "Ha van ilyen fiókod, elküldtük a levelet."
RESET_LINK_RE = re.compile(r"http://testserver(/jelszo-visszaallitas/[^/\s]+/[^/\s]+/)")
RESET_BODY_TEMPLATE = "accounts/email/password_reset_body.txt"


def make_user(email="anna@example.com", **extra):
    extra.setdefault("name", "Anna")
    return User.objects.create_user(email=email, password=PASSWORD, **extra)


class PasswordResetRequestTests(TestCase):
    url = reverse("password_reset")

    def setUp(self):
        cache.clear()
        self.anna = make_user()

    def request_reset(self, email="anna@example.com", client=None):
        return (client or self.client).post(self.url, {"email": email})

    def test_page_shows_the_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'name="email"')
        self.assertTemplateUsed(response, "base.html")

    def test_account_gets_one_reset_email_and_the_neutral_page(self):
        response = self.request_reset(email=" ANNA@Example.com ")
        self.assertRedirects(response, reverse("password_reset_sent"))
        self.assertEqual([m.to for m in mail.outbox], [["anna@example.com"]])
        self.assertRegex(mail.outbox[0].body, RESET_LINK_RE)
        self.assertContains(self.client.get(response["Location"]), NEUTRAL)

    def test_email_uses_site_name_and_says_to_ignore_it(self):
        with override_settings(SITE_NAME="Próba Műhely"):
            self.request_reset()
        message = mail.outbox[0]
        self.assertIn("Próba Műhely", message.subject)
        self.assertIn("Próba Műhely", message.body)
        self.assertNotIn("MesterKereső", message.subject + message.body)
        self.assertIn("Ha nem te kérted, hagyd figyelmen kívül", message.body)
        self.assertIn("1 óráig", message.body)

    def test_unverified_account_gets_a_reset_email(self):
        make_user(email="uj@example.com", email_verified=False)
        self.request_reset(email="uj@example.com")
        self.assertEqual([m.to for m in mail.outbox], [["uj@example.com"]])

    def test_staff_account_gets_a_reset_email(self):
        make_user(email="ugyfel@example.com", is_staff=True)
        self.request_reset(email="ugyfel@example.com")
        self.assertEqual([m.to for m in mail.outbox], [["ugyfel@example.com"]])

    def test_no_email_to_unknown_inactive_or_superuser_address(self):
        make_user(email="tiltott@example.com", is_active=False)
        User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        for email in ("nincs@example.com", "tiltott@example.com", "admin@example.com"):
            with self.subTest(email=email):
                self.assertRedirects(self.request_reset(email=email), reverse("password_reset_sent"))
        self.assertEqual(mail.outbox, [])

    def test_answer_is_byte_identical_whether_or_not_an_email_goes_out(self):
        make_user(email="tiltott@example.com", is_active=False)
        User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        responses = [
            self.request_reset(email=email, client=Client())
            for email in ("anna@example.com", "nincs@example.com", "tiltott@example.com", "admin@example.com")
        ]
        first = responses[0]
        for other in responses[1:]:
            self.assertEqual(other.status_code, first.status_code)
            self.assertEqual(other.content, first.content)
            self.assertEqual(dict(other.headers), dict(first.headers))
            self.assertEqual(other.cookies.output(), first.cookies.output())
        self.assertEqual([m.to for m in mail.outbox], [["anna@example.com"]])

    def test_unknown_address_builds_the_email_too(self):
        # Timing (K3): every branch does the same work; only the delivery itself is skipped.
        response = self.request_reset(email="nincs@example.com")
        self.assertIn(RESET_BODY_TEMPLATE, [t.name for t in response.templates])

    def test_at_most_one_email_a_minute(self):
        now = time.time()
        self.request_reset()
        self.request_reset()
        self.assertEqual(len(mail.outbox), 1)
        with mock.patch("time.time", return_value=now + 61):
            self.request_reset()
        self.assertEqual(len(mail.outbox), 2)

    def test_at_most_five_emails_an_hour(self):
        now = time.time()
        for minute in range(8):
            with mock.patch("time.time", return_value=now + minute * 61):
                self.request_reset()
        self.assertEqual(len(mail.outbox), 5)
        with mock.patch("time.time", return_value=now + 60 * 60 + 1):
            self.request_reset()
        self.assertEqual(len(mail.outbox), 6)

    def test_limited_request_gets_the_same_answer(self):
        first = self.request_reset(client=Client())
        limited = self.request_reset(client=Client())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(limited.content, first.content)
        self.assertEqual(dict(limited.headers), dict(first.headers))

    def test_invalid_address_shows_a_form_error_and_sends_nothing(self):
        response = self.request_reset(email="nem-email")
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(mail.outbox, [])

    def test_link_uses_the_request_host(self):
        with self.settings(ALLOWED_HOSTS=["mesterkereso.example"]):
            self.client.post(self.url, {"email": "anna@example.com"}, headers={"host": "mesterkereso.example"})
        self.assertIn("http://mesterkereso.example/jelszo-visszaallitas/", mail.outbox[0].body)

    def test_mail_failure_still_shows_the_neutral_page_and_logs_no_address(self):
        refused = smtplib.SMTPRecipientsRefused({"anna@example.com": (550, b"anna@example.com unknown")})
        failing_send = mock.patch("accounts.emails.send_mail", side_effect=refused)
        with failing_send, self.assertLogs("accounts.emails", level="ERROR") as logs:
            response = self.request_reset()
        self.assertRedirects(response, reverse("password_reset_sent"))
        self.assertNotIn("anna@example.com", "\n".join(logs.output))

    def test_emailed_link_moves_the_token_into_the_session(self):
        self.request_reset()
        path = RESET_LINK_RE.search(mail.outbox[0].body).group(1)
        token = path.rstrip("/").rsplit("/", 1)[1]
        response = self.client.get(path)
        fixed_path = path.replace(token, "uj-jelszo")
        self.assertRedirects(response, fixed_path, fetch_redirect_response=False)
        self.assertNotIn(token, response["Location"])
        self.assertEqual(self.client.get(fixed_path).status_code, 200)


NEW_PASSWORD = "Uj-titkos-jelszo-77"
INVALID_TITLE = "A link érvénytelen vagy lejárt"


def uid_of(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def reset_link(user, token=None):
    return reverse("password_reset_confirm", args=[uid_of(user), token or default_token_generator.make_token(user)])


def set_password_path(user):
    return reverse("password_reset_confirm", args=[uid_of(user), "uj-jelszo"])


class SetNewPasswordTests(TestCase):
    def setUp(self):
        cache.clear()
        self.anna = make_user(email="kovacs.anna@example.com", name="Szabó Benedikt", phone="+381641234567")

    def open_link(self, user=None, token=None):
        """Open the e-mailed link like a browser: the token goes into the session, then the fixed page loads."""
        user = user or self.anna
        response = self.client.get(reset_link(user, token), follow=True)
        return response

    def submit(self, password1=NEW_PASSWORD, password2=None, user=None):
        return self.client.post(
            set_password_path(user or self.anna),
            {"new_password1": password1, "new_password2": password2 if password2 is not None else password1},
        )

    def test_valid_link_shows_the_new_password_form(self):
        response = self.open_link()
        self.assertContains(response, 'name="new_password1"')
        self.assertContains(response, 'name="new_password2"')
        self.assertTemplateUsed(response, "base.html")

    def test_new_password_is_saved_and_leads_to_login(self):
        self.open_link()
        response = self.submit()
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.anna.refresh_from_db()
        self.assertTrue(self.anna.check_password(NEW_PASSWORD))

    def test_forged_token_shows_the_invalid_page(self):
        response = self.open_link(token="abc123-0123456789abcdef0123456789abcdef")
        self.assertContains(response, INVALID_TITLE)
        self.assertNotContains(response, 'name="new_password1"')

    def test_unknown_user_id_shows_the_invalid_page(self):
        response = self.client.get(reverse("password_reset_confirm", args=["bm9wZQ", "abc-123"]))
        self.assertContains(response, INVALID_TITLE)

    def test_token_of_another_user_does_not_work(self):
        other = make_user(email="bela@example.com", name="Béla")
        response = self.open_link(token=default_token_generator.make_token(other))
        self.assertContains(response, INVALID_TITLE)

    def test_expired_link_shows_the_invalid_page(self):
        made_at = datetime.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 60)
        with mock.patch.object(PasswordResetTokenGenerator, "_now", return_value=made_at):
            token = default_token_generator.make_token(self.anna)
        self.assertContains(self.open_link(token=token), INVALID_TITLE)

    def test_link_is_still_valid_just_before_one_hour(self):
        made_at = datetime.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT - 60)
        with mock.patch.object(PasswordResetTokenGenerator, "_now", return_value=made_at):
            token = default_token_generator.make_token(self.anna)
        self.assertContains(self.open_link(token=token), 'name="new_password1"')

    def test_used_link_does_not_work_again(self):
        token = default_token_generator.make_token(self.anna)
        self.open_link(token=token)
        self.submit()
        response = Client().get(reset_link(self.anna, token), follow=True)
        self.assertContains(response, INVALID_TITLE)

    def test_fixed_page_without_a_session_token_is_invalid(self):
        response = self.client.get(set_password_path(self.anna))
        self.assertContains(response, INVALID_TITLE)
        self.submit()
        self.anna.refresh_from_db()
        self.assertTrue(self.anna.check_password(PASSWORD))

    def test_session_token_only_works_for_its_own_user(self):
        other = make_user(email="bela@example.com", name="Béla")
        self.open_link()
        response = self.client.get(set_password_path(other))
        self.assertContains(response, INVALID_TITLE)

    def test_inactive_account_cannot_reset(self):
        token = default_token_generator.make_token(self.anna)
        User.objects.filter(pk=self.anna.pk).update(is_active=False)
        self.assertContains(self.open_link(token=token), INVALID_TITLE)

    def test_new_password_follows_the_registration_rules(self):
        cases = {
            "kovacs.anna@ex": "password_too_similar",  # e-mail
            "SzaboBenedikt": "password_too_similar",  # name
            "telefon+381641234567": "password_too_similar",  # phone
            "rovid1": "password_too_short",
            "password123": "password_too_common",
            "9876543210123": "password_entirely_numeric",
        }
        self.open_link()
        for password, code in cases.items():
            with self.subTest(password=password):
                response = self.submit(password)
                self.assertEqual(response.status_code, 200)
                codes = [e.code for errors in response.context["form"].errors.as_data().values() for e in errors]
                self.assertIn(code, codes)
        self.anna.refresh_from_db()
        self.assertTrue(self.anna.check_password(PASSWORD))

    def test_the_two_passwords_must_match(self):
        self.open_link()
        response = self.submit(NEW_PASSWORD, NEW_PASSWORD + "x")
        self.assertContains(response, "A két jelszó nem egyezik.")
        self.anna.refresh_from_db()
        self.assertTrue(self.anna.check_password(PASSWORD))

    def test_superuser_cannot_reset_even_with_a_valid_token(self):
        # E.g. promoted after the e-mail went out: superusers use "manage.py changepassword".
        token = default_token_generator.make_token(self.anna)
        User.objects.filter(pk=self.anna.pk).update(is_superuser=True, is_staff=True)
        self.assertContains(self.open_link(token=token), INVALID_TITLE)

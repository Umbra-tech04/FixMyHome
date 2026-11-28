import time
from unittest import mock

from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from accounts.tests.test_registration import valid_data

PASSWORD = "Jelszo-12345"
NEUTRAL = "Ha van ilyen fiók, elküldtük a levelet."
VERIFY_SUBJECT = f"{settings.SITE_NAME}: erősítsd meg az e-mail-címedet"


class ResendTests(TestCase):
    url = reverse("resend_verification")

    def setUp(self):
        cache.clear()
        self.anna = User.objects.create_user(
            email="anna@example.com", password=PASSWORD, name="Anna", email_verified=False,
        )

    def resend(self, email="anna@example.com", client=None):
        return (client or self.client).post(self.url, {"email": email})

    def test_page_shows_the_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'name="email"')
        self.assertTemplateUsed(response, "base.html")

    def test_unverified_account_gets_a_new_verification_email(self):
        response = self.resend(email=" ANNA@Example.com ")
        self.assertRedirects(response, reverse("resend_verification_sent"))
        self.assertEqual([(m.to, m.subject) for m in mail.outbox], [(["anna@example.com"], VERIFY_SUBJECT)])
        self.assertContains(self.client.get(response["Location"]), NEUTRAL)

    def test_answer_is_identical_whether_or_not_an_account_waits(self):
        User.objects.create_user(email="kesz@example.com", password=PASSWORD, name="Kész")  # verified
        User.objects.create_user(email="tiltott@example.com", password=PASSWORD, name="Tiltott",
                                 is_active=False, email_verified=False)
        responses = [
            self.resend(email=email, client=Client())
            for email in ("anna@example.com", "nincs@example.com", "kesz@example.com", "tiltott@example.com")
        ]
        first = responses[0]
        for other in responses[1:]:
            self.assertEqual(other.status_code, first.status_code)
            self.assertEqual(other.content, first.content)
            self.assertEqual(dict(other.headers), dict(first.headers))
            self.assertEqual(other.cookies.output(), first.cookies.output())
        self.assertEqual([m.to for m in mail.outbox], [["anna@example.com"]])  # only the waiting account

    def test_at_most_one_email_a_minute(self):
        now = time.time()
        self.resend()
        self.resend()
        self.assertEqual(len(mail.outbox), 1)
        with mock.patch("time.time", return_value=now + 61):
            self.resend()
        self.assertEqual(len(mail.outbox), 2)

    def test_at_most_five_emails_an_hour(self):
        now = time.time()
        for minute in range(8):
            with mock.patch("time.time", return_value=now + minute * 61):
                self.resend()
        self.assertEqual(len(mail.outbox), 5)
        with mock.patch("time.time", return_value=now + 60 * 60 + 1):
            self.resend()
        self.assertEqual(len(mail.outbox), 6)

    def test_limited_request_gets_the_same_answer(self):
        first = self.resend(client=Client())
        limited = self.resend(client=Client())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(limited.content, first.content)
        self.assertEqual(dict(limited.headers), dict(first.headers))

    def test_registration_email_counts_toward_the_limit(self):
        self.anna.delete()
        self.client.post(reverse("register"), valid_data())
        self.resend()
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_address_shows_a_form_error_and_sends_nothing(self):
        response = self.resend(email="nem-email")
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(mail.outbox, [])

    def test_emailed_link_verifies(self):
        self.resend()
        path = mail.outbox[0].body.split("http://testserver", 1)[1].split()[0]
        self.client.get(path)
        self.anna.refresh_from_db()
        self.assertTrue(self.anna.email_verified)


class ResendLinkTests(TestCase):
    """Every dead end of the flow points to the resend page."""

    resend_link = f'href="{reverse("resend_verification")}"'

    def test_invalid_link_page_links_to_resend(self):
        response = self.client.get(reverse("verify_email", args=["nem-token"]))
        self.assertContains(response, self.resend_link, status_code=400)

    def test_sent_page_links_to_resend(self):
        self.assertContains(self.client.get(reverse("verification_sent")), self.resend_link)

    def test_unverified_login_error_links_to_resend(self):
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna", email_verified=False)
        response = self.client.post(reverse("login"), {"username": "anna@example.com", "password": PASSWORD})
        self.assertContains(response, self.resend_link)  # a real link, not escaped text

    def test_unverified_admin_login_error_links_to_resend(self):
        User.objects.create_user(
            email="admin@example.com", password=PASSWORD, name="Admin", is_staff=True, email_verified=False,
        )
        response = self.client.post(
            reverse("admin:login"), {"username": "admin@example.com", "password": PASSWORD, "next": "/admin/"},
        )
        self.assertContains(response, self.resend_link)

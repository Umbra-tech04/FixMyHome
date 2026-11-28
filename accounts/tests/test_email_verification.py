import re
import smtplib
import time
from unittest import mock

from django.core import mail, signing
from django.test import TestCase
from django.urls import reverse

from accounts.models import MasterProfile, Role, User
from accounts.tests.test_registration import master_data, valid_data
from accounts.tokens import make_verification_token
from listings.geo import CITIES, nearby_masters
from listings.models import Category

PASSWORD = "Jelszo-12345"
DAY = 24 * 60 * 60
VERIFIED_MESSAGE = "Az e-mail-címedet megerősítettük, most már beléphetsz."
INVALID_TITLE = "A link érvénytelen vagy lejárt"
VERIFY_SUBJECT = "Erősítsd meg az e-mail-címedet a MesterKeresőn"
SENT_TITLE = "Elküldtük a levelet"
LINK_RE = re.compile(r"http://testserver(/email-megerosites/[^/\s]+/)")


def unverified_user(email="anna@example.com", **extra):
    return User.objects.create_user(email=email, password=PASSWORD, name="Anna", email_verified=False, **extra)


def unverified_master(email="bela@example.com"):
    user = unverified_user(email=email, role=Role.MASTER)
    MasterProfile.objects.create(
        user=user, profession=Category.objects.get(name="Festő"), service_area="Szabadka", contact="x",
        latitude=CITIES["Szabadka"][0], longitude=CITIES["Szabadka"][1], is_available=False,
    )
    return user


def verify_url(token):
    return reverse("verify_email", args=[token])


class VerifyLinkTests(TestCase):
    def test_valid_link_verifies_and_sends_to_login(self):
        user = unverified_user()
        response = self.client.get(verify_url(make_verification_token(user)), follow=True)
        self.assertRedirects(response, reverse("login"))
        self.assertContains(response, VERIFIED_MESSAGE)
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_link_does_not_log_in(self):
        user = unverified_user()
        self.client.get(verify_url(make_verification_token(user)))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_reusing_the_link_is_harmless(self):
        user = unverified_user()
        token = make_verification_token(user)
        self.client.get(verify_url(token))
        response = self.client.get(verify_url(token), follow=True)
        self.assertRedirects(response, reverse("login"))
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_expired_link_shows_error_page(self):
        user = unverified_user()
        token = make_verification_token(user)
        with mock.patch("django.core.signing.time.time", return_value=time.time() + DAY + 1):
            response = self.client.get(verify_url(token))
        self.assertContains(response, INVALID_TITLE, status_code=400)
        self.assertTemplateUsed(response, "base.html")
        user.refresh_from_db()
        self.assertFalse(user.email_verified)

    def test_forged_link_shows_error_page(self):
        user = unverified_user()
        token = make_verification_token(user)
        for forged in (token[:-2] + "xx", "nem-token", signing.dumps({"uid": user.pk, "email": user.email})):
            with self.subTest(forged=forged):
                self.assertContains(self.client.get(verify_url(forged)), INVALID_TITLE, status_code=400)
        user.refresh_from_db()
        self.assertFalse(user.email_verified)

    def test_link_of_another_user_does_not_verify_this_one(self):
        anna = unverified_user()
        bela = unverified_user(email="bela@example.com")
        mixed = signing.dumps({"uid": bela.pk, "email": anna.email}, salt="accounts.email-verification")
        self.assertContains(self.client.get(verify_url(mixed)), INVALID_TITLE, status_code=400)
        anna.refresh_from_db()
        bela.refresh_from_db()
        self.assertFalse(anna.email_verified)
        self.assertFalse(bela.email_verified)

    def test_link_for_old_address_is_rejected(self):
        user = unverified_user()
        token = make_verification_token(user)
        user.email = "anna.uj@example.com"
        user.save()
        self.assertContains(self.client.get(verify_url(token)), INVALID_TITLE, status_code=400)

    def test_inactive_account_is_not_verified(self):
        user = unverified_user(is_active=False)
        self.assertContains(self.client.get(verify_url(make_verification_token(user))), INVALID_TITLE, status_code=400)
        user.refresh_from_db()
        self.assertFalse(user.email_verified)


class MasterVisibilityTests(TestCase):
    def test_unverified_master_is_not_listed_until_verified(self):
        master = unverified_master()
        self.assertEqual(nearby_masters(*CITIES["Szabadka"], 10), [])
        self.client.get(verify_url(make_verification_token(master)))
        self.assertEqual([p.user for p in nearby_masters(*CITIES["Szabadka"], 10)], [master])

    def test_reused_link_does_not_override_a_later_unavailable_choice(self):
        master = unverified_master()
        token = make_verification_token(master)
        self.client.get(verify_url(token))
        MasterProfile.objects.filter(user=master).update(is_available=False)  # the master switched it off
        self.client.get(verify_url(token))
        self.assertFalse(MasterProfile.objects.get(user=master).is_available)


class RegistrationEmailTests(TestCase):
    url = reverse("register")

    def register(self, **overrides):
        return self.client.post(self.url, valid_data(**overrides))

    def test_registration_sends_one_verification_email_to_the_address(self):
        self.register(email="Anna@Example.com")
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["anna@example.com"])
        self.assertEqual(message.subject, VERIFY_SUBJECT)
        self.assertIn("Szia, Anna!", message.body)
        self.assertIn("A link 24 óráig érvényes.", message.body)
        self.assertIn("Ha nem te regisztráltál, ne kattints a linkre", message.body)
        self.assertRegex(message.body, LINK_RE)
        self.assertFalse(message.alternatives)  # plain text only

    def test_registration_redirects_to_sent_page_without_login(self):
        response = self.register()
        self.assertRedirects(response, reverse("verification_sent"))
        self.assertNotIn("_auth_user_id", self.client.session)
        page = self.client.get(reverse("verification_sent"))
        self.assertContains(page, SENT_TITLE)
        self.assertTemplateUsed(page, "base.html")

    def test_emailed_link_verifies_the_new_account(self):
        self.register()
        path = LINK_RE.search(mail.outbox[0].body).group(1)
        self.assertRedirects(self.client.get(path), reverse("login"))
        self.assertTrue(User.objects.get(email="anna@example.com").email_verified)

    def test_link_uses_the_request_host(self):
        with self.settings(ALLOWED_HOSTS=["mesterkereso.example"]):
            self.client.post(self.url, valid_data(), headers={"host": "mesterkereso.example"})
        self.assertIn("http://mesterkereso.example/email-megerosites/", mail.outbox[0].body)

    def test_foreign_host_header_is_refused(self):
        with self.settings(ALLOWED_HOSTS=["mesterkereso.example"]):
            response = self.client.post(self.url, valid_data(), headers={"host": "tamado.example"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(mail.outbox, [])
        self.assertFalse(User.objects.exists())

    def test_new_master_is_hidden_until_verified(self):
        self.client.post(self.url, master_data())
        master = User.objects.get(email="bela@example.com")
        self.assertFalse(master.master_profile.is_available)
        self.assertNotIn(master, [p.user for p in nearby_masters(*CITIES["Szabadka"], 50)])

    def test_mail_failure_still_shows_sent_page_and_logs_no_address(self):
        refused = smtplib.SMTPRecipientsRefused({"anna@example.com": (550, b"anna@example.com unknown")})
        failing_send = mock.patch("accounts.emails.send_mail", side_effect=refused)
        with failing_send, self.assertLogs("accounts.emails", level="ERROR") as logs:
            response = self.register()
        self.assertRedirects(response, reverse("verification_sent"))
        self.assertTrue(User.objects.filter(email="anna@example.com").exists())
        self.assertNotIn("anna@example.com", "\n".join(logs.output))

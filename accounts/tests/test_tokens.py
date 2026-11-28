import time
from unittest import mock

from django.core import signing
from django.test import TestCase

from accounts.models import User
from accounts.tokens import VERIFICATION_SALT, make_verification_token, user_from_verification_token

PASSWORD = "Jelszo-12345"
DAY = 24 * 60 * 60


class VerificationTokenTests(TestCase):
    def setUp(self):
        self.anna = User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        self.bela = User.objects.create_user(email="bela@example.com", password=PASSWORD, name="Béla")

    def test_valid_token_returns_its_user(self):
        self.assertEqual(user_from_verification_token(make_verification_token(self.anna)), self.anna)

    def test_tokens_differ_per_user(self):
        self.assertNotEqual(make_verification_token(self.anna), make_verification_token(self.bela))

    def test_token_is_valid_just_under_24_hours(self):
        token = make_verification_token(self.anna)
        with mock.patch("django.core.signing.time.time", return_value=time.time() + DAY - 60):
            self.assertEqual(user_from_verification_token(token), self.anna)

    def test_expired_token_is_rejected(self):
        token = make_verification_token(self.anna)
        with mock.patch("django.core.signing.time.time", return_value=time.time() + DAY + 1):
            self.assertIsNone(user_from_verification_token(token))

    def test_tampered_token_is_rejected(self):
        token = make_verification_token(self.anna)
        payload, rest = token.split(":", 1)
        forged_payload = signing.b64_encode(b'{"uid":%d,"email":"bela@example.com"}' % self.bela.pk).decode()
        for forged in (token[:-1] + ("A" if token[-1] != "A" else "B"), f"{forged_payload}:{rest}", payload):
            with self.subTest(forged=forged):
                self.assertIsNone(user_from_verification_token(forged))

    def test_garbage_is_rejected(self):
        for garbage in ("", "x", "a:b:c", "%%%", "ł" * 50):
            with self.subTest(garbage=garbage):
                self.assertIsNone(user_from_verification_token(garbage))

    def test_token_signed_with_another_salt_is_rejected(self):
        payload = {"uid": self.anna.pk, "email": self.anna.email}
        for salt in ("django.core.signing", "accounts.other-purpose"):
            with self.subTest(salt=salt):
                self.assertIsNone(user_from_verification_token(signing.dumps(payload, salt=salt)))

    def test_token_of_another_user_does_not_match(self):
        # Even a correctly signed payload is refused if the id and the e-mail belong to different users.
        mixed = signing.dumps({"uid": self.bela.pk, "email": self.anna.email}, salt=VERIFICATION_SALT)
        self.assertIsNone(user_from_verification_token(mixed))

    def test_email_change_invalidates_token(self):
        token = make_verification_token(self.anna)
        self.anna.email = "anna.uj@example.com"
        self.anna.save()
        self.assertIsNone(user_from_verification_token(token))

    def test_deleted_user_token_is_rejected(self):
        token = make_verification_token(self.anna)
        self.anna.delete()
        self.assertIsNone(user_from_verification_token(token))

    def test_malformed_payload_is_rejected(self):
        for payload in (["x"], {"uid": "abc", "email": "anna@example.com"}, {"email": "anna@example.com"}, 42):
            with self.subTest(payload=payload):
                self.assertIsNone(user_from_verification_token(signing.dumps(payload, salt=VERIFICATION_SALT)))

import hashlib
import time
from unittest import mock

from django.core import signing
from django.test import TestCase, override_settings
from django.utils.crypto import salted_hmac

from accounts.models import User
from accounts.tokens import (
    EMAIL_HASH_SALT,
    VERIFICATION_SALT,
    email_hash,
    make_verification_token,
    user_from_verification_token,
)

PASSWORD = "Jelszo-12345"
DAY = 24 * 60 * 60


def keyed(email):
    return salted_hmac(EMAIL_HASH_SALT, email, algorithm="sha256").hexdigest()


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
        forged_json = '{"uid":%d,"email_hash":"%s"}' % (self.bela.pk, keyed("bela@example.com"))
        forged_payload = signing.b64_encode(forged_json.encode()).decode()
        for forged in (token[:-1] + ("A" if token[-1] != "A" else "B"), f"{forged_payload}:{rest}", payload):
            with self.subTest(forged=forged):
                self.assertIsNone(user_from_verification_token(forged))

    def test_garbage_is_rejected(self):
        for garbage in ("", "x", "a:b:c", "%%%", "ł" * 50):
            with self.subTest(garbage=garbage):
                self.assertIsNone(user_from_verification_token(garbage))

    def test_token_signed_with_another_salt_is_rejected(self):
        payload = {"uid": self.anna.pk, "email_hash": keyed(self.anna.email)}
        for salt in ("django.core.signing", "accounts.other-purpose"):
            with self.subTest(salt=salt):
                self.assertIsNone(user_from_verification_token(signing.dumps(payload, salt=salt)))

    def test_token_of_another_user_does_not_match(self):
        # Even a correctly signed payload is refused if the id and the e-mail belong to different users.
        mixed = signing.dumps({"uid": self.bela.pk, "email_hash": keyed(self.anna.email)}, salt=VERIFICATION_SALT)
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
        anna_hash = keyed(self.anna.email)
        payloads = (
            ["x"], 42, {"uid": "abc", "email_hash": anna_hash}, {"email_hash": anna_hash}, {"uid": self.anna.pk},
            {"uid": self.anna.pk, "email_hash": 42},
            {"uid": self.anna.pk, "email": self.anna.email},  # the old format, with the address in the clear
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertIsNone(user_from_verification_token(signing.dumps(payload, salt=VERIFICATION_SALT)))

    def test_token_holds_a_keyed_hash_of_the_address_not_the_address(self):
        token = make_verification_token(self.anna)
        payload = signing.loads(token, salt=VERIFICATION_SALT)
        self.assertEqual(payload, {"uid": self.anna.pk, "email_hash": keyed("anna@example.com")})
        decoded = signing.b64_decode(token.split(":", 1)[0].encode()).decode()
        self.assertNotIn("anna@example.com", decoded)
        self.assertNotIn("anna", token)

    def test_hash_uses_the_lowercased_trimmed_address(self):
        # The model lowercases on save; the hash normalises too, so a stray capital cannot break the link.
        token = make_verification_token(self.anna)
        User.objects.filter(pk=self.anna.pk).update(email="  Anna@Example.com ")
        self.assertEqual(user_from_verification_token(token).pk, self.anna.pk)

    def test_hash_is_keyed_so_a_guessed_address_cannot_be_checked(self):
        # Without SECRET_KEY nobody can compute the value for a guessed address and compare it with a logged token.
        token_hash = signing.loads(make_verification_token(self.anna), salt=VERIFICATION_SALT)["email_hash"]
        self.assertNotEqual(token_hash, hashlib.sha256(b"anna@example.com").hexdigest())
        self.assertEqual(len(token_hash), 64)  # HMAC-SHA256, not the SHA-1 default of salted_hmac

    def test_hash_depends_on_secret_key_and_salt(self):
        with override_settings(SECRET_KEY="another-secret-key-for-this-test-only-0123456789"):
            other_key = email_hash("anna@example.com")
        self.assertNotEqual(email_hash("anna@example.com"), other_key)
        other_salt = salted_hmac(VERIFICATION_SALT, "anna@example.com", algorithm="sha256").hexdigest()
        self.assertNotEqual(email_hash("anna@example.com"), other_salt)

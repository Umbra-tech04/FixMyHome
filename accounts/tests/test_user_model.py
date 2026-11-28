from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Role, User


class UserModelTests(TestCase):
    def test_default_role_is_user(self):
        user = User.objects.create_user(email="anna@example.com", password="Jelszo-12345", name="Anna")
        self.assertEqual(user.role, Role.USER)

    def test_login_identifier_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_email_is_stored_lowercase(self):
        user = User.objects.create_user(email="Anna@Example.COM", password="Jelszo-12345", name="Anna")
        user.refresh_from_db()
        self.assertEqual(user.email, "anna@example.com")

    def test_email_must_be_unique(self):
        User.objects.create_user(email="anna@example.com", password="Jelszo-12345", name="Anna")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(email="anna@example.com", password="Jelszo-12345", name="Anna 2")

    def test_get_by_natural_key_is_case_insensitive(self):
        user = User.objects.create_user(email="anna@example.com", password="Jelszo-12345", name="Anna")
        self.assertEqual(User.objects.get_by_natural_key("ANNA@Example.com"), user)

    def test_create_superuser_sets_staff_and_superuser_flags(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="Jelszo-12345", name="Admin")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class EmailVerifiedDefaultTests(TestCase):
    """Every account created outside the registration form counts as verified (seed_demo, admin, createsuperuser)."""

    def test_create_user_is_verified_by_default(self):
        user = User.objects.create_user(email="anna@example.com", password="Jelszo-12345", name="Anna")
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_seed_like_update_or_create_is_verified(self):
        # The same call shape as listings/management/commands/seed_demo.py.
        user, _ = User.objects.update_or_create(
            email="seed@example.com", defaults={"name": "Seed", "role": Role.MASTER, "phone": "+381601112222"},
        )
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_create_superuser_is_verified(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="Jelszo-12345", name="Admin")
        admin.refresh_from_db()
        self.assertTrue(admin.email_verified)

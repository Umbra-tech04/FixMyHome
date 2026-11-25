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

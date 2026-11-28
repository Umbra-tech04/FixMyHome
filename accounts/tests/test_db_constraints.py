"""Database rules on accounts: they hold even when save() and validation are bypassed.

Each IntegrityError test goes around the Python checks (queryset.update, bulk_create); the ValidationError
tests show the friendly message the admin and forms give instead.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User

PASSWORD = "Jelszo-12345"


def make_user(email="anna@example.com", **fields):
    return User.objects.create_user(email=email, password=PASSWORD, name="Anna", **fields)


class CaseInsensitiveEmailTests(TestCase):
    def setUp(self):
        self.anna = make_user("anna@example.com")

    def test_update_to_case_only_duplicate_is_rejected_by_the_database(self):
        bela = make_user("bela@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=bela.pk).update(email="ANNA@example.com")

    def test_bulk_create_of_case_only_duplicate_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="Anna@Example.com", name="Anna 2")])

    def test_different_addresses_are_allowed(self):
        User.objects.bulk_create([User(email="Bela@Example.com", name="Béla")])
        self.assertEqual(User.objects.count(), 2)

    def test_validate_constraints_gives_the_friendly_message(self):
        with self.assertRaises(ValidationError) as ctx:
            User(email="ANNA@example.com", name="Anna 2").validate_constraints()
        self.assertIn("Ezzel az e-mail-címmel már van fiók.", ctx.exception.messages)


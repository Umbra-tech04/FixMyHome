from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import MasterProfile, Role, User
from listings.models import Category


class MasterProfileTests(TestCase):
    def test_one_profile_per_user(self):
        user = User.objects.create_user(email="bela@example.com", password="Jelszo-12345", name="Béla", role=Role.MASTER)
        category = Category.objects.get(name="Villanyszerelő")
        MasterProfile.objects.create(user=user, profession=category, service_area="Szabadka", contact="+381 60 000 000")
        with self.assertRaises(IntegrityError), transaction.atomic():
            MasterProfile.objects.create(user=user, profession=category, service_area="Palics", contact="x")

    def test_coordinates_are_optional(self):
        user = User.objects.create_user(email="bela@example.com", password="Jelszo-12345", name="Béla", role=Role.MASTER)
        profile = MasterProfile.objects.create(
            user=user, profession=Category.objects.get(name="Festő"), service_area="Szabadka", contact="x",
        )
        self.assertIsNone(profile.latitude)
        self.assertIsNone(profile.longitude)

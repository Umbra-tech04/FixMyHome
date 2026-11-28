from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User

PASSWORD = "Jelszo-12345"


class UserAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        self.client.force_login(self.admin)
        User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")

    def test_admin_add_user_with_case_only_duplicate_email_shows_form_error(self):
        response = self.client.post(reverse("admin:accounts_user_add"), {
            "email": "ANNA@example.com", "name": "Anna 2", "role": Role.USER,
            "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["adminform"].form.errors.get("email"))
        self.assertEqual(User.objects.count(), 2)

    def test_model_validation_rejects_case_only_duplicate_email(self):
        with self.assertRaises(ValidationError) as ctx:
            User(email="ANNA@Example.com", name="Anna 2").full_clean(exclude=["password"])
        self.assertIn("email", ctx.exception.message_dict)


class EmailVerifiedAdminTests(TestCase):
    def setUp(self):
        from accounts.models import MasterProfile
        from listings.models import Category

        self.admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        self.client.force_login(self.admin)
        self.anna = User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna",
                                             email_verified=False)
        self.bela = User.objects.create_user(email="bela@example.com", password=PASSWORD, name="Béla",
                                             role=Role.MASTER, email_verified=False)
        self.profile = MasterProfile.objects.create(
            user=self.bela, profession=Category.objects.get(name="Festő"), service_area="Szabadka", contact="x",
            is_available=False,
        )

    def test_list_shows_and_filters_email_verified(self):
        response = self.client.get(reverse("admin:accounts_user_changelist"), {"email_verified__exact": "0"})
        self.assertContains(response, "e-mail megerősítve")
        self.assertEqual(
            sorted(u.email for u in response.context["cl"].result_list), ["anna@example.com", "bela@example.com"],
        )

    def test_change_form_has_the_field(self):
        response = self.client.get(reverse("admin:accounts_user_change", args=[self.anna.pk]))
        self.assertContains(response, 'name="email_verified"')

    def test_action_verifies_selected_accounts_and_shows_masters(self):
        response = self.client.post(reverse("admin:accounts_user_changelist"), {
            "action": "mark_email_verified", "_selected_action": [self.anna.pk, self.bela.pk],
        }, follow=True)
        self.assertContains(response, "2 fiók e-mail-címe megerősítve.")
        self.assertTrue(User.objects.filter(email_verified=False).count() == 0)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_available)

    def test_action_leaves_already_verified_masters_profile_alone(self):
        User.objects.filter(pk=self.bela.pk).update(email_verified=True)  # verified, and chose "unavailable"
        self.client.post(reverse("admin:accounts_user_changelist"), {
            "action": "mark_email_verified", "_selected_action": [self.bela.pk],
        })
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_available)

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

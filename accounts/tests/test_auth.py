from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User

PASSWORD = "Jelszo-12345"


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="anna@example.com", password=PASSWORD, name="Anna")
        self.login_url = reverse("login")

    def login_data(self, **overrides):
        data = {"username": "anna@example.com", "password": PASSWORD}
        data.update(overrides)
        return data

    def assertLoggedIn(self):
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def assertAnonymous(self):
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_with_email_and_password(self):
        response = self.client.post(self.login_url, self.login_data())
        self.assertRedirects(response, reverse("home"))
        self.assertLoggedIn()

    def test_login_is_case_insensitive_for_email(self):
        self.client.post(self.login_url, self.login_data(username="ANNA@Example.com"))
        self.assertLoggedIn()

    def test_wrong_password_shows_error(self):
        response = self.client.post(self.login_url, self.login_data(password="rossz-jelszo"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertAnonymous()

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, self.login_data())
        self.assertEqual(response.status_code, 200)
        self.assertAnonymous()

    def test_login_ignores_external_next(self):
        response = self.client.post(f"{self.login_url}?next=https://masik-oldal.example/", self.login_data())
        self.assertRedirects(response, reverse("home"))

    def test_logout_post_logs_out(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertAnonymous()

    def test_logout_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        self.assertLoggedIn()


class NavigationTests(TestCase):
    def test_navigation_for_anonymous_and_logged_in(self):
        anonymous = self.client.get(reverse("home"))
        self.assertContains(anonymous, "Belépés")
        self.assertContains(anonymous, "Regisztráció")
        self.assertNotContains(anonymous, "Kilépés")

        user = User.objects.create_user(email="bela@example.com", password=PASSWORD, name="Béla", role=Role.MASTER)
        self.client.force_login(user)
        logged_in = self.client.get(reverse("home"))
        self.assertContains(logged_in, "Béla")
        self.assertContains(logged_in, "Mester")
        self.assertContains(logged_in, "Kilépés")
        self.assertNotContains(logged_in, "Regisztráció")


class LoggedInRedirectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="anna@example.com", password="Jelszo-12345", name="Anna")
        self.client.force_login(self.user)

    def test_logged_in_user_is_redirected_from_register(self):
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("register"))
                self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(User.objects.count(), 1)

    def test_logged_in_user_is_redirected_from_login(self):
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_anonymous_user_still_sees_both_pages(self):
        self.client.logout()
        for name in ("register", "login"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from unittest import mock

from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from dotenv import dotenv_values

from config.security import DEV_SECRET_KEYS, env_bool, env_choice, env_int, validate_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent
# Csak tesztekhez: hosszú, de nem titkos kulcs.
STRONG_KEY = "test-only-" + "x1y2z3" * 10
HTTPS_EXPR = (
    "s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.SECURE_SSL_REDIRECT,"
    " s.SECURE_HSTS_SECONDS, getattr(s, 'SECURE_PROXY_SSL_HEADER', None)"
)


class ValidateSecretKeyTests(SimpleTestCase):
    def test_debug_mode_accepts_any_key(self):
        validate_secret_key("short", debug=True)

    def test_rejects_missing_key(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_secret_key("", debug=False)

    def test_rejects_short_key(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_secret_key("a" * 49, debug=False)

    def test_rejects_django_insecure_prefix(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_secret_key("django-insecure-" + "a" * 60, debug=False)

    def test_rejects_known_development_keys(self):
        for key in DEV_SECRET_KEYS:
            with self.subTest(key=key), self.assertRaises(ImproperlyConfigured):
                validate_secret_key(key, debug=False)

    def test_accepts_long_random_key(self):
        validate_secret_key(STRONG_KEY, debug=False)

    def test_error_message_does_not_leak_the_key(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_secret_key("a" * 49, debug=False)
        self.assertNotIn("a" * 49, str(ctx.exception))

    def test_env_example_key_is_listed_as_development_key(self):
        values = dotenv_values(BASE_DIR / ".env.example")
        self.assertIn(values["SECRET_KEY"], DEV_SECRET_KEYS)


class EnvBoolTests(SimpleTestCase):
    def test_missing_value_uses_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(env_bool("FLAG", True))
            self.assertFalse(env_bool("FLAG", False))

    def test_accepts_one_and_zero(self):
        with mock.patch.dict(os.environ, {"ON": "1", "OFF": "0"}):
            self.assertTrue(env_bool("ON", False))
            self.assertFalse(env_bool("OFF", True))

    def test_rejects_other_values(self):
        with mock.patch.dict(os.environ, {"FLAG": "yes"}), self.assertRaises(ImproperlyConfigured):
            env_bool("FLAG", False)


class EnvIntTests(SimpleTestCase):
    def test_missing_value_uses_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(env_int("NUM", 7, min_value=0), 7)

    def test_reads_integer(self):
        with mock.patch.dict(os.environ, {"NUM": " 42 "}):
            self.assertEqual(env_int("NUM", 7, min_value=0), 42)

    def test_rejects_non_integer(self):
        for value in ("abc", "1.5", "1e3"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"NUM": value}):
                with self.assertRaisesMessage(ImproperlyConfigured, "NUM"):
                    env_int("NUM", 7, min_value=0)

    def test_rejects_value_below_minimum(self):
        with mock.patch.dict(os.environ, {"NUM": "0"}):
            with self.assertRaisesMessage(ImproperlyConfigured, "NUM"):
                env_int("NUM", 7, min_value=1)

    def test_rejects_value_above_maximum(self):
        with mock.patch.dict(os.environ, {"NUM": "70000"}):
            with self.assertRaisesMessage(ImproperlyConfigured, "NUM"):
                env_int("NUM", 7, min_value=1, max_value=65535)


class EnvChoiceTests(SimpleTestCase):
    def test_missing_value_uses_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(env_choice("MODE", "console", ("console", "smtp")), "console")

    def test_reads_allowed_value(self):
        with mock.patch.dict(os.environ, {"MODE": " smtp "}):
            self.assertEqual(env_choice("MODE", "console", ("console", "smtp")), "smtp")

    def test_rejects_other_values(self):
        with mock.patch.dict(os.environ, {"MODE": "sendgrid"}):
            with self.assertRaisesMessage(ImproperlyConfigured, "MODE"):
                env_choice("MODE", "console", ("console", "smtp"))


TUNNEL_HOST = "pelda.trycloudflare.com"
TUNNEL_ORIGIN = f"https://{TUNNEL_HOST}"


@override_settings(ALLOWED_HOSTS=[TUNNEL_HOST], CSRF_TRUSTED_ORIGINS=[], SECURE_SSL_REDIRECT=True)
class BehindTunnelTests(TestCase):
    """The tunnel talks plain HTTP to Django; the visitor's browser uses HTTPS."""

    def get_login(self, client, **headers):
        return client.get(reverse("login"), headers={"host": TUNNEL_HOST, **headers})

    def test_without_trusted_proxy_header_ssl_redirect_loops(self):
        response = self.get_login(self.client, x_forwarded_proto="https")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], f"{TUNNEL_ORIGIN}{reverse('login')}")

    @override_settings(SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"))
    def test_with_trusted_proxy_header_page_loads(self):
        self.assertEqual(self.get_login(self.client, x_forwarded_proto="https").status_code, 200)

    def post_login(self, **headers):
        client = Client(enforce_csrf_checks=True)
        token = self.get_login(client, **headers).context["csrf_token"]
        return client.post(
            reverse("login"), {"csrfmiddlewaretoken": token, "username": "x@example.com", "password": "x"},
            headers={"host": TUNNEL_HOST, "origin": TUNNEL_ORIGIN, "referer": f"{TUNNEL_ORIGIN}/", **headers},
        )

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_csrf_fails_without_trusted_origin_or_proxy_header(self):
        self.assertEqual(self.post_login().status_code, 403)

    @override_settings(SECURE_SSL_REDIRECT=False, CSRF_TRUSTED_ORIGINS=[TUNNEL_ORIGIN])
    def test_csrf_passes_with_exact_trusted_origin(self):
        self.assertEqual(self.post_login().status_code, 200)

    @override_settings(SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"))
    def test_csrf_passes_with_trusted_proxy_header(self):
        self.assertEqual(self.post_login(x_forwarded_proto="https").status_code, 200)


class HomePageTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MesterKereső")


def load_settings(extra_env, dotenv_text=None, expr="s.DEBUG, s.SECRET_KEY"):
    """Betölti a beállításokat külön folyamatban, tiszta környezettel."""
    with tempfile.TemporaryDirectory() as tmp:
        dotenv = Path(tmp) / ".env"
        if dotenv_text is not None:
            dotenv.write_text(dotenv_text)
        env = {"PATH": os.environ["PATH"], "DOTENV_FILE": str(dotenv), **extra_env}
        return subprocess.run(
            [sys.executable, "-c", f"import config.settings as s; print({expr})"],
            cwd=BASE_DIR, env=env, capture_output=True, text=True,
        )


class SettingsEnvironmentTests(TestCase):
    def test_secret_key_is_required_when_debug_is_off(self):
        result = load_settings({})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)

    def test_debug_mode_works_without_secret_key(self):
        result = load_settings({"DEBUG": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("True"))

    def test_dotenv_file_is_loaded(self):
        result = load_settings({}, dotenv_text="DEBUG=1\nSECRET_KEY=from-dotenv\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True from-dotenv")

    def test_weak_secret_key_stops_startup_when_debug_is_off(self):
        result = load_settings({"DEBUG": "0", "SECRET_KEY": "csak-fejlesztesi-kulcs"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ImproperlyConfigured", result.stderr)

    def test_strong_secret_key_starts_when_debug_is_off(self):
        result = load_settings({"DEBUG": "0", "SECRET_KEY": STRONG_KEY}, expr="s.DEBUG")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False")

    def test_https_settings_are_off_in_debug_mode(self):
        result = load_settings({"DEBUG": "1"}, expr=HTTPS_EXPR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False False False 0 None")

    def test_https_settings_default_to_secure_when_debug_is_off(self):
        result = load_settings({"DEBUG": "0", "SECRET_KEY": STRONG_KEY}, expr=HTTPS_EXPR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True True True 3600 None")

    def test_ssl_redirect_and_hsts_can_be_set_from_environment(self):
        result = load_settings(
            {"DEBUG": "0", "SECRET_KEY": STRONG_KEY, "SECURE_SSL_REDIRECT": "0", "SECURE_HSTS_SECONDS": "0"},
            expr=HTTPS_EXPR,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True True False 0 None")

    def test_proxy_ssl_header_is_trusted_only_when_enabled(self):
        result = load_settings(
            {"DEBUG": "0", "SECRET_KEY": STRONG_KEY, "TRUST_PROXY_SSL_HEADER": "1"},
            expr="s.SECURE_PROXY_SSL_HEADER",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "('HTTP_X_FORWARDED_PROTO', 'https')")

    def test_invalid_boolean_env_value_stops_startup(self):
        result = load_settings({"DEBUG": "0", "SECRET_KEY": STRONG_KEY, "SECURE_SSL_REDIRECT": "yes"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECURE_SSL_REDIRECT", result.stderr)

    def test_invalid_hsts_seconds_stops_startup_with_clear_message(self):
        result = load_settings({"DEBUG": "0", "SECRET_KEY": STRONG_KEY, "SECURE_HSTS_SECONDS": "egy óra"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ImproperlyConfigured", result.stderr)
        self.assertIn("SECURE_HSTS_SECONDS", result.stderr)

    def test_allowed_hosts_and_csrf_origins_come_from_environment(self):
        result = load_settings(
            {"DEBUG": "1", "ALLOWED_HOSTS": ".trycloudflare.com,localhost",
             "CSRF_TRUSTED_ORIGINS": "https://*.trycloudflare.com"},
            expr="s.ALLOWED_HOSTS, s.CSRF_TRUSTED_ORIGINS",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "['.trycloudflare.com', 'localhost'] ['https://*.trycloudflare.com']",
        )


EMAIL_EXPR = "s.EMAIL_BACKEND, s.EMAIL_HOST, s.EMAIL_PORT, s.EMAIL_USE_TLS, s.EMAIL_TIMEOUT"


class EmailSettingsTests(TestCase):
    def test_console_backend_by_default(self):
        result = load_settings({"DEBUG": "1"}, expr=EMAIL_EXPR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(), "django.core.mail.backends.console.EmailBackend  587 True 10",
        )

    def test_smtp_settings_come_from_environment(self):
        env = {
            "DEBUG": "1", "EMAIL_BACKEND": "smtp", "EMAIL_HOST": "smtp.example.com", "EMAIL_PORT": "2525",
            "EMAIL_USE_TLS": "0", "EMAIL_HOST_USER": "mailer", "EMAIL_HOST_PASSWORD": "helyorzo",
            "DEFAULT_FROM_EMAIL": "MesterKereso <noreply@example.com>",
        }
        result = load_settings(
            env, expr=EMAIL_EXPR + ", s.EMAIL_HOST_USER, s.EMAIL_HOST_PASSWORD == 'helyorzo', s.DEFAULT_FROM_EMAIL",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "django.core.mail.backends.smtp.EmailBackend smtp.example.com 2525 False 10 mailer True "
            "MesterKereso <noreply@example.com>",
        )

    def test_unknown_backend_stops_startup(self):
        result = load_settings({"DEBUG": "1", "EMAIL_BACKEND": "sendgrid"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EMAIL_BACKEND", result.stderr)

    def test_smtp_without_host_stops_startup(self):
        result = load_settings({"DEBUG": "1", "EMAIL_BACKEND": "smtp"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EMAIL_HOST", result.stderr)

    def test_invalid_port_stops_startup(self):
        for port in ("abc", "0", "70000"):
            with self.subTest(port=port):
                result = load_settings({"DEBUG": "1", "EMAIL_PORT": port})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("EMAIL_PORT", result.stderr)

    def test_password_is_not_in_startup_errors(self):
        result = load_settings({"DEBUG": "1", "EMAIL_BACKEND": "smtp", "EMAIL_HOST_PASSWORD": "titkos-jelszo-123"})
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("titkos-jelszo-123", result.stderr)

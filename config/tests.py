import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from dotenv import dotenv_values

from config.security import DEV_SECRET_KEYS, validate_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent
# Csak tesztekhez: hosszú, de nem titkos kulcs.
STRONG_KEY = "test-only-" + "x1y2z3" * 10


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

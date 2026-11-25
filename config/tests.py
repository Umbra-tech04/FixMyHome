import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

BASE_DIR = Path(__file__).resolve().parent.parent


class HomePageTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MesterKereső")


def load_settings(extra_env, dotenv_text=None):
    """Betölti a beállításokat külön folyamatban, tiszta környezettel."""
    with tempfile.TemporaryDirectory() as tmp:
        dotenv = Path(tmp) / ".env"
        if dotenv_text is not None:
            dotenv.write_text(dotenv_text)
        env = {"PATH": os.environ["PATH"], "DOTENV_FILE": str(dotenv), **extra_env}
        return subprocess.run(
            [sys.executable, "-c", "import config.settings as s; print(s.DEBUG, s.SECRET_KEY)"],
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

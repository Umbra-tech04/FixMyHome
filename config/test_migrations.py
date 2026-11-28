"""The database-rule migrations (accounts 0006, listings 0004) on existing data.

Each test steps the schema back to the state before them, writes rows with the historical models (no save()
normalisation, no validation, as old data or a raw import would be), then migrates forward.
"""

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from config.migration_checks import DataCheckError

BEFORE = [("accounts", "0005_user_email_verified"), ("listings", "0003_application_message_alter_ad_status")]


def migrate(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection).loader.project_state(targets).apps


def latest():
    return MigrationExecutor(connection).loader.graph.leaf_nodes()


class ConstraintMigrationTestCase(TransactionTestCase):
    # The data migration listings 0002 (categories) is restored for later TransactionTestCases.
    serialized_rollback = True

    def setUp(self):
        # Registered first, so it runs even if a test (or the rest of setUp) fails: the other tests need the
        # latest schema. Rows left behind could break the forward migration, so they go first.
        self.addCleanup(self._back_to_latest)
        self.old = migrate(BEFORE)

    def _back_to_latest(self):
        call_command("flush", verbosity=0, interactive=False, inhibit_post_migrate=True)
        migrate(latest())

    def make_user(self, email, **fields):
        User = self.old.get_model("accounts", "User")
        return User.objects.create(email=email, name="Teszt Elek", password="!", **fields)

    def migrate_forward(self):
        return migrate(latest())


class ForwardAndBackTests(ConstraintMigrationTestCase):
    def test_valid_data_migrates_forward_back_and_forward_again(self):
        self.make_user("anna@example.com")
        self.make_user("bela@example.com")

        new = self.migrate_forward()
        self.assertEqual(new.get_model("accounts", "User").objects.count(), 2)
        migrate(BEFORE)
        new = self.migrate_forward()
        self.assertEqual(new.get_model("accounts", "User").objects.count(), 2)


class CaseOnlyDuplicateEmailTests(ConstraintMigrationTestCase):
    def test_stops_with_a_readable_message_and_keeps_both_accounts(self):
        first = self.make_user("Anna@Example.com")
        second = self.make_user("anna@example.com")

        with self.assertRaises(DataCheckError) as ctx:
            self.migrate_forward()

        message = str(ctx.exception)
        self.assertIn("A migráció leállt", message)
        self.assertIn(f"#{first.pk} Anna@Example.com", message)
        self.assertIn(f"#{second.pk} anna@example.com", message)
        User = self.old.get_model("accounts", "User")
        self.assertEqual(
            sorted(User.objects.values_list("email", flat=True)), ["Anna@Example.com", "anna@example.com"],
        )


class BrokenValueRuleTests(ConstraintMigrationTestCase):
    def test_bad_master_coordinates_and_role_stop_the_migration_and_stay_unchanged(self):
        master = self.make_user("mester@example.com", role="master")
        stranger = self.make_user("bela@example.com", role="boss")
        Category = self.old.get_model("listings", "Category")
        MasterProfile = self.old.get_model("accounts", "MasterProfile")
        profile = MasterProfile.objects.create(
            user=master, profession=Category.objects.get(name="Vízszerelő"), service_area="Szabadka",
            contact="-", latitude=95.0, longitude=None,
        )

        with self.assertRaises(DataCheckError) as ctx:
            self.migrate_forward()

        message = str(ctx.exception)
        self.assertIn("A migráció leállt", message)
        self.assertIn(f"accounts_user_role_valid): Érvénytelen szerepkör. Sorok: #{stranger.pk}", message)
        self.assertIn(f"accounts_masterprofile_latitude_range): A szélesség -90 és 90 fok között lehet. "
                      f"Sorok: #{profile.pk}", message)
        self.assertIn(f"accounts_masterprofile_coordinates_together)", message)
        profile.refresh_from_db()
        self.assertEqual((profile.latitude, profile.longitude), (95.0, None))

"""Indexes exist for real queries only; this checks that the query they were made for can use them."""

from unittest import skipUnless

from django.db import connection
from django.test import TestCase

from listings.models import Ad, Category


@skipUnless(connection.vendor == "sqlite", "EXPLAIN QUERY PLAN is SQLite's; PostgreSQL may prefer a seq scan on tiny tables")
class OpenAdsByCategoryIndexTests(TestCase):
    def test_nearby_open_ads_query_uses_the_category_status_index(self):
        # The query of listings.geo.nearby_open_ads (the master's home page, listings.views.master_ads).
        qs = Ad.objects.filter(
            status=Ad.Status.OPEN, category=Category.objects.first(), latitude__isnull=False, longitude__isnull=False,
        ).select_related("category")
        sql, params = qs.query.sql_with_params()
        with connection.cursor() as cursor:
            cursor.execute("EXPLAIN QUERY PLAN " + sql, params)
            plan = " | ".join(row[-1] for row in cursor.fetchall())
        self.assertIn("USING INDEX ad_category_status_idx (category_id=? AND status=?)", plan)

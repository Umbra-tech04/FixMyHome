from django.db import migrations

CATEGORIES = [
    "Vízszerelő", "Villanyszerelő", "Festő", "Hegesztő", "Asztalos",
    "Kőműves", "Fűtésszerelő", "Burkoló", "Lakatos", "Tetőfedő",
]


def seed(apps, schema_editor):
    Category = apps.get_model("listings", "Category")
    for name in CATEGORIES:
        Category.objects.get_or_create(name=name)


def unseed(apps, schema_editor):
    Category = apps.get_model("listings", "Category")
    Category.objects.filter(name__in=CATEGORIES, ad__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("listings", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]

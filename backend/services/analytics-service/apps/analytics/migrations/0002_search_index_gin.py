# Generated for LearnGrid LMS T-018 search reporting analytics.

from django.db import migrations


def create_search_text_gin_index(_apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        CREATE INDEX IF NOT EXISTS gin_search_index_search_text
        ON search_index_records
        USING GIN (to_tsvector('simple', search_text));
        """
    )


def drop_search_text_gin_index(_apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP INDEX IF EXISTS gin_search_index_search_text;")


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_search_text_gin_index, drop_search_text_gin_index),
    ]

from django.db import migrations, models


def add_layout_when_missing(apps, schema_editor):
    """Support databases that received this column before migration tracking."""
    PrintTemplate = apps.get_model('printing', 'PrintTemplate')
    table_name = PrintTemplate._meta.db_table
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(), table_name
        )
    }
    if 'layout' in existing_columns:
        return
    field = models.JSONField(blank=True, default=dict)
    field.set_attributes_from_name('layout')
    schema_editor.add_field(PrintTemplate, field)


class Migration(migrations.Migration):
    dependencies = [('printing', '0003_constraints')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_layout_when_missing, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='printtemplate',
                    name='layout',
                    field=models.JSONField(blank=True, default=dict),
                ),
            ],
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounting', '0004_bankaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='bank_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='expenses', to='accounting.bankaccount'),
        ),
    ]

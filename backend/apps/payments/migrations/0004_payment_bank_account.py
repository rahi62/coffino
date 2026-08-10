from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounting', '0004_bankaccount'),
        ('payments', '0003_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='bank_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='payments', to='accounting.bankaccount'),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounting', '0005_expense_bank_account'),
        ('purchasing', '0003_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierpayment',
            name='bank_account',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='supplier_payments', to='accounting.bankaccount',
            ),
        ),
    ]

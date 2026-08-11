from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('purchasing', '0004_supplierpayment_bank_account')]

    operations = [
        migrations.AddField(
            model_name='purchaseinvoice',
            name='purchaser_name',
            field=models.CharField(blank=True, max_length=140),
        ),
    ]

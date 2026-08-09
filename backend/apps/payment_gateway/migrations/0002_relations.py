from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('payment_gateway', '0001_initial'),
        ('payments', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='paymentgatewayconfig', name='branch', field=models.OneToOneField('businesses.branch', on_delete=models.CASCADE, related_name='payment_gateway')),
        migrations.AddField(model_name='gatewayintent', name='payment', field=models.OneToOneField('payments.payment', on_delete=models.CASCADE, related_name='gateway_intent')),
    ]

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('giftcards', '0001_initial'),
        ('orders', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='giftcard', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='gift_cards')),
        migrations.AddField(model_name='giftcardtransaction', name='card', field=models.ForeignKey('giftcards.giftcard', on_delete=models.PROTECT, related_name='transactions')),
        migrations.AddField(model_name='giftcardtransaction', name='order', field=models.ForeignKey('orders.order', null=True, blank=True, on_delete=models.SET_NULL, related_name='gift_card_transactions')),
    ]

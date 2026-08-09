from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('giftcards', '0001_initial'),
        ('orders', '0001_initial'),
        ('payments', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='payment', name='order', field=models.ForeignKey('orders.order', on_delete=models.CASCADE, related_name='payments')),
        migrations.AddField(model_name='payment', name='bill_split', field=models.ForeignKey('payments.billsplit', null=True, blank=True, on_delete=models.SET_NULL, related_name='payments')),
        migrations.AddField(model_name='payment', name='gift_card', field=models.ForeignKey('giftcards.giftcard', null=True, blank=True, on_delete=models.SET_NULL, related_name='payments')),
        migrations.AddField(model_name='payment', name='received_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='refund', name='payment', field=models.ForeignKey('payments.payment', on_delete=models.PROTECT, related_name='refunds')),
        migrations.AddField(model_name='refund', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='billsplit', name='order', field=models.ForeignKey('orders.order', on_delete=models.CASCADE, related_name='bill_splits')),
        migrations.AddField(model_name='billsplitline', name='split', field=models.ForeignKey('payments.billsplit', on_delete=models.CASCADE, related_name='lines')),
        migrations.AddField(model_name='billsplitline', name='order_item', field=models.ForeignKey('orders.orderitem', on_delete=models.PROTECT, related_name='split_lines')),
    ]

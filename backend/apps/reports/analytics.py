from decimal import Decimal
from django.db.models import Sum, Count
from django.db.models.functions import ExtractHour
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, Refund

def sales_analytics(branch,start=None,end=None):
    orders=Order.objects.filter(branch=branch).exclude(status=Order.Status.CANCELLED)
    if start: orders=orders.filter(created_at__date__gte=start)
    if end: orders=orders.filter(created_at__date__lte=end)
    items=OrderItem.objects.filter(order__in=orders)
    by_item=list(items.values('product_name').annotate(quantity=Sum('quantity'),revenue=Sum('line_total')).order_by('-revenue')[:100])
    by_category=list(items.values('product__category__name').annotate(quantity=Sum('quantity'),revenue=Sum('line_total')).order_by('-revenue'))
    by_hour=list(orders.annotate(hour=ExtractHour('created_at')).values('hour').annotate(orders=Count('id'),revenue=Sum('grand_total')).order_by('hour'))
    cashier=list(Payment.objects.filter(order__in=orders,status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED,Payment.Status.REFUNDED]).values('received_by__id','received_by__username','received_by__first_name','received_by__last_name').annotate(transactions=Count('id'),collected=Sum('amount')).order_by('-collected'))
    for row in cashier:
        uid=row['received_by__id']
        refs=Refund.objects.filter(payment__order__in=orders,payment__received_by_id=uid).aggregate(v=Sum('amount'))['v'] or 0
        row['refunds']=refs; row['net_collected']=Decimal(row['collected'] or 0)-Decimal(refs)
    return {'by_item':by_item,'by_category':by_category,'by_hour':by_hour,'cashiers':cashier}

from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.db.models.functions import ExtractHour, TruncDate
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, Refund

def sales_analytics(branch,start=None,end=None):
    orders=Order.objects.filter(branch=branch).exclude(status=Order.Status.CANCELLED)
    if start: orders=orders.filter(created_at__date__gte=start)
    if end: orders=orders.filter(created_at__date__lte=end)
    items=OrderItem.objects.filter(order__in=orders)
    refunds=Refund.objects.filter(payment__order__in=orders).aggregate(v=Sum('amount'))['v'] or 0
    aggregates=orders.aggregate(
        gross_sales=Sum('grand_total'),
        discounts=Sum('discount_total'),
        orders=Count('id'),
        average_order_value=Avg('grand_total'),
    )
    item_count=items.aggregate(v=Sum('quantity'))['v'] or 0
    by_item=list(items.values('product_name').annotate(quantity=Sum('quantity'),revenue=Sum('line_total')).order_by('-revenue')[:100])
    by_category=list(items.values('product__category__name').annotate(quantity=Sum('quantity'),revenue=Sum('line_total')).order_by('-revenue'))
    by_hour=list(orders.annotate(hour=ExtractHour('created_at')).values('hour').annotate(orders=Count('id'),revenue=Sum('grand_total')).order_by('hour'))
    by_day=list(orders.annotate(day=TruncDate('created_at')).values('day').annotate(orders=Count('id'),revenue=Sum('grand_total')).order_by('day'))
    by_order_type=list(orders.values('order_type').annotate(orders=Count('id'),revenue=Sum('grand_total')).order_by('-revenue'))
    cashier=list(Payment.objects.filter(order__in=orders,status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED,Payment.Status.REFUNDED]).values('received_by__id','received_by__username','received_by__first_name','received_by__last_name').annotate(transactions=Count('id'),collected=Sum('amount')).order_by('-collected'))
    for row in cashier:
        uid=row['received_by__id']
        refs=Refund.objects.filter(payment__order__in=orders,payment__received_by_id=uid).aggregate(v=Sum('amount'))['v'] or 0
        row['refunds']=refs; row['net_collected']=Decimal(row['collected'] or 0)-Decimal(refs)
    gross_sales=aggregates['gross_sales'] or 0
    return {
        'summary':{
            'gross_sales':gross_sales,
            'refunds':refunds,
            'net_sales':Decimal(gross_sales)-Decimal(refunds),
            'discounts':aggregates['discounts'] or 0,
            'orders':aggregates['orders'] or 0,
            'items':item_count,
            'average_order_value':aggregates['average_order_value'] or 0,
        },
        'by_item':by_item,
        'by_category':by_category,
        'by_hour':by_hour,
        'by_day':by_day,
        'by_order_type':by_order_type,
        'cashiers':cashier,
    }

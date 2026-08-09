from decimal import Decimal
from django.db.models import Sum, Count, F
from django.utils import timezone
from apps.inventory.models import StockMovement, WasteRecord, InventoryItem
from apps.orders.models import Order, OrderItem
from apps.payments.models import Refund
from apps.reports.services import profit_report, _snapshot_or_fallback, recognized_order_revenue

def _q(qs,start,end,field='created_at'):
    if start:qs=qs.filter(**{field+'__date__gte':start})
    if end:qs=qs.filter(**{field+'__date__lte':end})
    return qs

def food_cost_report(branch,start=None,end=None):
    orders=Order.objects.filter(branch=branch).exclude(status=Order.Status.CANCELLED)
    orders=_q(orders,start,end)
    gross=Decimal(orders.aggregate(v=Sum('grand_total'))['v'] or 0)
    refunds=Decimal(Refund.objects.filter(payment__order__in=orders).aggregate(v=Sum('amount'))['v'] or 0)
    revenue=sum((recognized_order_revenue(o) for o in orders.select_related('branch')),Decimal('0'))
    order_items=OrderItem.objects.filter(order__in=orders).select_related('product').prefetch_related('product__recipe_items__inventory_item')
    theoretical=sum((_snapshot_or_fallback(x)*Decimal(x.quantity) for x in order_items),Decimal('0'))
    waste=_q(WasteRecord.objects.filter(branch=branch),start,end)
    waste_cost=Decimal(waste.aggregate(v=Sum('total_cost'))['v'] or 0)
    total_food_cost=theoretical+waste_cost
    pct=(total_food_cost/revenue*Decimal('100')) if revenue>0 else None
    waste_pct=(waste_cost/revenue*Decimal('100')) if revenue>0 else None
    top=list(waste.values('item__name','reason').annotate(quantity=Sum('quantity'),cost=Sum('total_cost')).order_by('-cost')[:20])
    return {
        'revenue':revenue,'theoretical_consumption_cost':theoretical,'waste_cost':waste_cost,
        'actual_food_cost':total_food_cost,'food_cost_percent':pct,'waste_percent_of_revenue':waste_pct,
        'top_waste':top,
    }
def multi_branch_dashboard(business):
    today=timezone.localdate();month_start=today.replace(day=1)
    rows=[]
    for branch in business.branches.filter(is_active=True):
        today_orders=Order.objects.filter(branch=branch,created_at__date=today).exclude(status=Order.Status.CANCELLED)
        fin=profit_report(branch,str(month_start),str(today))
        fc=food_cost_report(branch,str(month_start),str(today))
        rows.append({
            'branch_id':branch.id,'branch_name':branch.name,
            'today_sales':today_orders.aggregate(v=Sum('grand_total'))['v'] or 0,
            'today_orders':today_orders.count(),
            'month_revenue':fin['revenue'],'month_net_profit':fin['net_profit'],
            'food_cost_percent':fc['food_cost_percent'],
            'low_stock':InventoryItem.objects.filter(branch=branch,current_stock__lte=F('minimum_stock')).count(),
        })
    return {'business':business.name,'branches':rows,'totals':{
        'today_sales':sum((Decimal(x['today_sales']) for x in rows),Decimal('0')),
        'month_revenue':sum((Decimal(x['month_revenue']) for x in rows),Decimal('0')),
        'month_net_profit':sum((Decimal(x['month_net_profit']) for x in rows),Decimal('0')),
    }}

from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.accounting.models import Expense, FixedOverhead
from apps.payments.models import Refund

def _monthly_equivalent(overhead):
    a=Decimal(overhead.amount)
    if overhead.frequency=='DAILY': return a*Decimal('30')
    if overhead.frequency=='YEARLY': return a/Decimal('12')
    return a

def _snapshot_or_fallback(oi):
    snap=Decimal(oi.unit_cost_snapshot or 0)
    if snap>0:return snap
    return sum((Decimal(r.quantity)*Decimal(r.inventory_item.average_cost) for r in oi.product.recipe_items.all()),Decimal('0'))


def recognized_order_tax(order):
    refunded=Decimal(Refund.objects.filter(payment__order=order).aggregate(v=Sum('amount'))['v'] or 0)
    grand=Decimal(order.grand_total or 0)
    ratio=max(Decimal('0'),Decimal('1')-(refunded/grand)) if grand>0 else Decimal('0')
    return Decimal(order.tax_total or 0)*ratio

def recognized_order_revenue(order):
    from apps.payments.models import Refund
    refunded=Decimal(Refund.objects.filter(payment__order=order).aggregate(v=Sum('amount'))['v'] or 0)
    grand=Decimal(order.grand_total or 0)
    ratio=max(Decimal('0'),Decimal('1')-(refunded/grand)) if grand>0 else Decimal('0')
    tax=recognized_order_tax(order)
    service=Decimal(order.service_charge_total or 0)*ratio
    collected=max(Decimal('0'),grand-refunded)
    try: service_is_revenue=order.branch.fiscal_settings.service_charge_is_revenue
    except Exception: service_is_revenue=True
    return collected-tax-(Decimal('0') if service_is_revenue else service)

def profit_report(branch,start=None,end=None):
    qs=Order.objects.filter(branch=branch).exclude(status=Order.Status.CANCELLED)
    if start: qs=qs.filter(created_at__date__gte=start)
    if end: qs=qs.filter(created_at__date__lte=end)
    gross_sales=Decimal(qs.aggregate(v=Sum('grand_total'))['v'] or 0)
    refunds=Decimal(Refund.objects.filter(payment__order__in=qs).aggregate(v=Sum('amount'))['v'] or 0)
    tax_collected=sum((recognized_order_tax(o) for o in qs.select_related('branch','branch__fiscal_settings')),Decimal('0'))
    revenue=sum((recognized_order_revenue(o) for o in qs.select_related('branch','branch__fiscal_settings')),Decimal('0'))
    items=OrderItem.objects.filter(order__in=qs).select_related('product').prefetch_related('product__recipe_items__inventory_item')
    cogs=sum((_snapshot_or_fallback(oi)*Decimal(oi.quantity) for oi in items),Decimal('0'))
    expenses=Expense.objects.filter(branch=branch)
    if start: expenses=expenses.filter(occurred_at__date__gte=start)
    if end: expenses=expenses.filter(occurred_at__date__lte=end)
    variable_expense=Decimal(expenses.aggregate(v=Sum('amount'))['v'] or 0)
    monthly_overhead=sum((_monthly_equivalent(x) for x in FixedOverhead.objects.filter(branch=branch,is_active=True)),Decimal('0'))
    gross=revenue-cogs; contribution=gross-variable_expense; net=contribution-monthly_overhead
    orders=qs.count(); avg_order=(revenue/Decimal(orders)) if orders else Decimal('0')
    variable_per_order=((cogs+variable_expense)/Decimal(orders)) if orders else Decimal('0')
    contribution_per_order=avg_order-variable_per_order
    break_even_orders=(monthly_overhead/contribution_per_order) if contribution_per_order>0 else None
    break_even_revenue=(break_even_orders*avg_order) if break_even_orders is not None else None
    return {'gross_sales':gross_sales,'refunds':refunds,'tax_collected':tax_collected,'revenue':revenue,'cogs':cogs,'gross_profit':gross,'expenses':variable_expense,'monthly_overhead':monthly_overhead,'net_profit':net,'orders':orders,'average_order_value':avg_order,'contribution_margin':contribution,'contribution_per_order':contribution_per_order,'break_even_orders':break_even_orders,'break_even_revenue':break_even_revenue}

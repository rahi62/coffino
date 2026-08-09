from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from apps.orders.models import Order, OrderItem
from apps.payments.models import Refund
from apps.workforce.models import Attendance
from apps.cashier.models import DailyClosing
from apps.inventory.models import InventoryItem
from .services import profit_report
from .food_cost import food_cost_report

def management_kpis(branch,start=None,end=None):
    today=timezone.localdate()
    start=start or str(today.replace(day=1));end=end or str(today)
    orders=Order.objects.filter(branch=branch,created_at__date__gte=start,created_at__date__lte=end).exclude(status=Order.Status.CANCELLED)
    fin=profit_report(branch,start,end);food=food_cost_report(branch,start,end)
    refunds=Decimal(Refund.objects.filter(payment__order__in=orders).aggregate(v=Sum('amount'))['v'] or 0)
    gross=Decimal(orders.aggregate(v=Sum('grand_total'))['v'] or 0)
    refund_rate=(refunds/gross*Decimal('100')) if gross>0 else Decimal('0')
    attendance=Attendance.objects.filter(branch=branch,clock_in__date__gte=start,clock_in__date__lte=end)
    labor_minutes=0
    for a in attendance:
        if a.clock_out: labor_minutes+=max(0,int((a.clock_out-a.clock_in).total_seconds()//60))
    labor_hours=Decimal(labor_minutes)/Decimal('60')
    sales_per_labor_hour=(Decimal(fin['revenue'])/labor_hours) if labor_hours>0 else None
    closings=DailyClosing.objects.filter(branch=branch,business_date__gte=start,business_date__lte=end)
    cash_variance=sum((abs(Decimal(x.cash_difference)) for x in closings),Decimal('0'))
    top=OrderItem.objects.filter(order__in=orders).values('product_name').annotate(revenue=Sum('line_total'),quantity=Sum('quantity')).order_by('-revenue').first()
    gross_margin_pct=(Decimal(fin['gross_profit'])/Decimal(fin['revenue'])*Decimal('100')) if Decimal(fin['revenue'])>0 else None
    return {
        'start':start,'end':end,'orders':orders.count(),'net_revenue':fin['revenue'],
        'average_ticket':fin['average_order_value'],'gross_margin_percent':gross_margin_pct,
        'food_cost_percent':food['food_cost_percent'],'waste_cost':food['waste_cost'],
        'refund_rate_percent':refund_rate,'labor_hours':labor_hours,
        'sales_per_labor_hour':sales_per_labor_hour,'cash_variance_absolute':cash_variance,
        'break_even_revenue':fin['break_even_revenue'],
        'low_stock_count':sum(1 for x in InventoryItem.objects.filter(branch=branch) if x.current_stock<=x.minimum_stock),
        'top_product':top,
    }

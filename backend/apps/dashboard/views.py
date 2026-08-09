from django.db.models import F, Sum
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.permissions import has_perm
from apps.core.tenancy import resolve_branch_for_user
from apps.inventory.models import InventoryItem
from apps.orders.models import Order
from apps.reports.services import profit_report


@api_view(["GET"])
def dashboard(request):
    if not (has_perm(request.user,'orders.view') or has_perm(request.user,'reports.view')):
        return Response({'detail':'دسترسی به داشبورد ندارید'},status=403)

    try:
        branch=resolve_branch_for_user(request.user,request.query_params.get('branch'))
    except Exception:
        return Response(
            {'detail':'برای این کاربر شعبه داشبورد معتبر یا مجاز نیست'},
            status=403
        )

    today=timezone.localdate()
    qs=Order.objects.filter(branch=branch,created_at__date=today)
    active=qs.exclude(status=Order.Status.CANCELLED)

    response={
        "branch":branch.id,
        "sales_today":active.aggregate(v=Sum("grand_total"))["v"] or 0,
        "orders_today":active.count(),
        "open_orders":qs.exclude(
            status__in=[Order.Status.COMPLETED,Order.Status.CANCELLED]
        ).count(),
        "ready_orders":qs.filter(status=Order.Status.READY).count(),
        "low_stock":None,
        "month_net_profit":None,
        "month_revenue":None,
        "break_even_revenue":None,
        "break_even_orders":None,
    }

    if has_perm(request.user,'inventory.view'):
        response["low_stock"]=InventoryItem.objects.filter(
            branch=branch,current_stock__lte=F("minimum_stock")
        ).count()

    if has_perm(request.user,'reports.view'):
        month_start=today.replace(day=1)
        fin=profit_report(branch,start=str(month_start),end=str(today))
        response.update({
            "month_net_profit":fin["net_profit"],
            "month_revenue":fin["revenue"],
            "break_even_revenue":fin["break_even_revenue"],
            "break_even_orders":fin["break_even_orders"],
        })

    return Response(response)

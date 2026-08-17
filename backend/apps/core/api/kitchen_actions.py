from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.permissions import has_perm
from apps.core.serializers import KitchenTicketSerializer
from apps.core.tenancy import can_access_branch
from apps.kitchen.models import KitchenTicket
from apps.loyalty.services import earn_order_points
from apps.orders.models import Order


@api_view(['POST'])
def kitchen_ticket_done(request,pk):
    """Mark a READY kitchen ticket as handed over without forcing payment on dine-in orders."""
    if not has_perm(request.user,'kitchen.update'):
        return Response({'detail':'دسترسی ندارید'},status=403)
    try:
        ticket=KitchenTicket.objects.select_related('order__branch').get(pk=pk)
    except KitchenTicket.DoesNotExist:
        return Response({'detail':'تیکت یافت نشد'},status=404)
    if not can_access_branch(request.user,ticket.order.branch):
        return Response({'detail':'دسترسی ندارید'},status=403)
    if ticket.status!=KitchenTicket.Status.READY:
        return Response({'detail':'فقط تیکت آماده قابل تحویل است'},status=409)

    ticket.status=KitchenTicket.Status.DONE
    ticket.save(update_fields=['status','updated_at'])
    order=ticket.order

    if not order.kitchen_tickets.exclude(status=KitchenTicket.Status.DONE).exists():
        settled_states={
            Order.PaymentStatus.PAID,
            Order.PaymentStatus.PARTIALLY_REFUNDED,
            Order.PaymentStatus.REFUNDED,
        }
        if order.payment_status in settled_states:
            order.status=Order.Status.COMPLETED
            order.save(update_fields=['status','updated_at'])
            earn_order_points(order)
            try:
                online=order.online_order
                online.status='COMPLETED'
                online.save(update_fields=['status','updated_at'])
            except Exception:
                pass
        elif order.status!=Order.Status.CANCELLED:
            # Dine-in/pay-later: preparation is handed over but the commercial order remains open.
            order.status=Order.Status.READY
            order.save(update_fields=['status','updated_at'])

    return Response(KitchenTicketSerializer(ticket).data)

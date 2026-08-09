from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from apps.cashier.models import CashShift, CashMovement


def active_shift_for(branch, user=None):
    qs=CashShift.objects.filter(register__branch=branch,is_open=True).select_related('register').order_by('-opened_at')
    if user: qs=qs.filter(cashier=user)
    return qs.first()

@transaction.atomic
def record_cash_movement(*, branch, movement_type, amount, user=None, payment=None, note='', reference_type='', reference_id=''):
    shift=active_shift_for(branch,user) or active_shift_for(branch)
    if not shift: raise ValueError('برای عملیات نقدی ابتدا شیفت صندوق را باز کنید')
    return CashMovement.objects.create(shift=shift,movement_type=movement_type,amount=Decimal(amount),note=note,payment=payment,reference_type=reference_type,reference_id=str(reference_id or ''),created_by=user)

@transaction.atomic
def close_shift(shift, actual_cash):
    shift=CashShift.objects.select_for_update().get(pk=shift.pk)
    if not shift.is_open: raise ValueError('شیفت بسته است')
    movements=shift.movements.all()
    cash_in=movements.filter(movement_type__in=[CashMovement.Type.SALE,CashMovement.Type.CASH_IN]).aggregate(v=Sum('amount'))['v'] or 0
    cash_out=movements.filter(movement_type__in=[CashMovement.Type.REFUND,CashMovement.Type.CASH_OUT,CashMovement.Type.EXPENSE,CashMovement.Type.SUPPLIER_PAYMENT]).aggregate(v=Sum('amount'))['v'] or 0
    expected=Decimal(shift.opening_balance)+Decimal(cash_in)-Decimal(cash_out)
    shift.expected_cash=expected; shift.closing_balance=actual_cash; shift.difference=Decimal(actual_cash)-expected; shift.is_open=False; shift.closed_at=timezone.now()
    shift.save(update_fields=['expected_cash','closing_balance','difference','is_open','closed_at','updated_at'])
    return shift

@transaction.atomic
def close_business_day(*,branch,business_date,counted_cash,user):
    from django.db.models import Sum
    from apps.orders.models import Order
    from apps.payments.models import Payment, Refund
    from apps.accounting.models import Expense
    from apps.cashier.models import DailyClosing
    from apps.audit.services import log_action
    if DailyClosing.objects.filter(branch=branch,business_date=business_date).exists():
        raise ValueError('این روز قبلاً بسته شده است')
    orders=Order.objects.filter(branch=branch,created_at__date=business_date).exclude(status=Order.Status.CANCELLED)
    gross=Decimal(orders.aggregate(v=Sum('grand_total'))['v'] or 0)
    refunds=Decimal(Refund.objects.filter(payment__order__in=orders).aggregate(v=Sum('amount'))['v'] or 0)
    cash=Decimal(Payment.objects.filter(order__in=orders,method='CASH',status__in=['SUCCEEDED','PARTIALLY_REFUNDED','REFUNDED']).aggregate(v=Sum('amount'))['v'] or 0)
    pos=Decimal(Payment.objects.filter(order__in=orders,method='POS',status__in=['SUCCEEDED','PARTIALLY_REFUNDED','REFUNDED']).aggregate(v=Sum('amount'))['v'] or 0)
    cash_refunds=Decimal(Refund.objects.filter(payment__order__in=orders,method='CASH').aggregate(v=Sum('amount'))['v'] or 0)
    expenses=Decimal(Expense.objects.filter(branch=branch,occurred_at__date=business_date).aggregate(v=Sum('amount'))['v'] or 0)
    day_shifts=CashShift.objects.filter(register__branch=branch,opened_at__date=business_date)
    opening=sum((Decimal(x.opening_balance) for x in day_shifts),Decimal('0'))
    movements=CashMovement.objects.filter(shift__in=day_shifts)
    ledger_in=Decimal(movements.filter(movement_type__in=[CashMovement.Type.SALE,CashMovement.Type.CASH_IN]).aggregate(v=Sum('amount'))['v'] or 0)
    ledger_out=Decimal(movements.filter(movement_type__in=[CashMovement.Type.REFUND,CashMovement.Type.CASH_OUT,CashMovement.Type.EXPENSE,CashMovement.Type.SUPPLIER_PAYMENT]).aggregate(v=Sum('amount'))['v'] or 0)
    expected=opening+ledger_in-ledger_out
    counted=Decimal(str(counted_cash))
    obj=DailyClosing.objects.create(branch=branch,business_date=business_date,gross_sales=gross,refunds=refunds,net_sales=gross-refunds,cash_sales=cash,pos_sales=pos,expenses=expenses,expected_cash=expected,counted_cash=counted,cash_difference=counted-expected,closed_by=user,snapshot={'orders':orders.count()})
    CashShift.objects.filter(register__branch=branch,is_open=True).update(is_open=False,closed_at=timezone.now())
    log_action(actor=user,branch=branch,action='DAILY_CLOSE',entity=obj,description=f'بستن روز {business_date}',after={'net_sales':str(obj.net_sales),'cash_difference':str(obj.cash_difference)})
    return obj

from decimal import Decimal
from django.db import transaction
from apps.accounting.models import Expense
from apps.cashier.models import CashMovement
from apps.cashier.services import record_cash_movement

@transaction.atomic
def create_expense(*, branch, title, amount, occurred_at, category=None, payment_method='CASH', notes='', user=None):
    amount=Decimal(str(amount))
    if amount<=0: raise ValueError('مبلغ هزینه باید بیشتر از صفر باشد')
    e=Expense.objects.create(branch=branch,category=category,title=title,amount=amount,payment_method=payment_method,occurred_at=occurred_at,notes=notes,created_by=user)
    if payment_method=='CASH':
        record_cash_movement(branch=branch,movement_type=CashMovement.Type.EXPENSE,amount=amount,user=user,note=title,reference_type='Expense',reference_id=e.id)
    return e

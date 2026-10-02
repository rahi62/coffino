from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.db.models import Sum
from .models import Payment, BillSplit, BillSplitLine
from apps.orders.models import Order
from apps.cashier.models import CashMovement
from apps.cashier.services import record_cash_movement

_PERSIAN_DIGITS=str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789')

def payment_amount(value, *, field_label='مبلغ پرداخت'):
    normalized=str(value if value is not None else '').translate(_PERSIAN_DIGITS).replace('٬','').replace(',','').strip()
    try:
        amount=Decimal(normalized)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f'{field_label} معتبر نیست')
    if not amount.is_finite() or amount!=amount.to_integral_value():
        raise ValueError(f'{field_label} باید یک عدد صحیح به ریال باشد')
    return amount

def successful_paid_amount(order):
    return Decimal(order.payments.filter(status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED,Payment.Status.REFUNDED]).aggregate(v=Sum('amount'))['v'] or 0)


def resolve_bank_account(order, *, account_id, method):
    """Return a usable account only when it belongs to the order branch."""
    if not account_id:
        return None
    if method not in {Payment.Method.POS, Payment.Method.ONLINE}:
        raise ValueError('انتخاب حساب فقط برای کارت‌خوان یا پرداخت آنلاین مجاز است')
    from apps.accounting.models import BankAccount
    try:
        account = BankAccount.objects.select_for_update().get(pk=account_id)
    except (BankAccount.DoesNotExist, TypeError, ValueError):
        raise ValueError('حساب یا کارت بانکی انتخاب‌شده معتبر نیست')
    if account.branch_id != order.branch_id or not account.is_active:
        raise ValueError('حساب یا کارت بانکی انتخاب‌شده برای این شعبه قابل استفاده نیست')
    return account

@transaction.atomic
def settle_order(order,*,payments,user=None,require_full=True):
    order=Order.objects.select_for_update().get(pk=order.pk)
    existing=successful_paid_amount(order)
    remaining=max(Decimal('0'),Decimal(order.grand_total)-existing)
    rows=[];new_total=Decimal('0')
    for row in payments or []:
        amount=payment_amount(row.get('amount',0))
        if amount<=0: raise ValueError('مبلغ پرداخت باید مثبت باشد')
        method=row.get('method')
        if method not in dict(Payment.Method.choices): raise ValueError('روش پرداخت نامعتبر است')
        tendered=payment_amount(row.get('tendered_amount',amount),field_label='وجه دریافتی')
        if method==Payment.Method.CASH and tendered<amount: raise ValueError('وجه دریافتی کمتر از مبلغ نقدی است')
        change=(tendered-amount) if method==Payment.Method.CASH else Decimal('0')
        rows.append((amount,method,tendered,change,row.get('reference_number',''),row.get('payer_label',''),row.get('gift_card_code',''),row.get('bank_account')))
        new_total+=amount
    if require_full and new_total!=remaining:
        raise ValueError(f'جمع پرداخت‌ها باید دقیقاً {remaining} باشد')
    if new_total>remaining: raise ValueError('جمع پرداخت بیشتر از مانده سفارش است')
    created=[]
    for amount,method,tendered,change,ref,payer_label,gift_code,bank_account_id in rows:
        gift_card=None
        bank_account=resolve_bank_account(order,account_id=bank_account_id,method=method)
        if method==Payment.Method.WALLET:
            if not order.customer_id:raise ValueError('پرداخت کیف پول نیازمند مشتری است')
            from apps.loyalty.services import debit_wallet
            debit_wallet(order.customer,amount,order=order,reference=f'Order #{order.order_number}')
        elif method==Payment.Method.GIFT_CARD:
            if not gift_code:raise ValueError('کد کارت هدیه لازم است')
            from apps.giftcards.services import debit_card
            gift_card=debit_card(branch=order.branch,code=gift_code,amount=amount,order=order)
        p=Payment.objects.create(order=order,amount=amount,method=method,status=Payment.Status.SUCCEEDED,reference_number=ref,payer_label=payer_label,tendered_amount=tendered,change_amount=change,gift_card=gift_card,bank_account=bank_account,received_by=user)
        if method==Payment.Method.CASH:
            record_cash_movement(branch=order.branch,movement_type=CashMovement.Type.SALE,amount=amount,user=user,payment=p,note=f'فروش سفارش #{order.order_number}',reference_type='Order',reference_id=order.id)
        created.append(p)
    total=existing+new_total
    order.payment_status=Order.PaymentStatus.PAID if total>=Decimal(order.grand_total) else (Order.PaymentStatus.PARTIAL if total>0 else Order.PaymentStatus.UNPAID)
    order.save(update_fields=['payment_status','updated_at'])
    return created


def _allocate_component(total,weights):
    total=Decimal(total);weight_sum=sum(weights,Decimal('0'));out=[];used=Decimal('0')
    for i,w in enumerate(weights):
        if i==len(weights)-1:v=total-used
        else:v=(total*w/weight_sum).quantize(Decimal('1')) if weight_sum else Decimal('0')
        out.append(v);used+=v
    return out

@transaction.atomic
def create_item_splits(order,groups):
    order=Order.objects.select_for_update().prefetch_related('items').get(pk=order.pk)
    if order.payment_status!=Order.PaymentStatus.UNPAID or order.payments.filter(status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED,Payment.Status.REFUNDED]).exists():raise ValueError('Item Split باید قبل از اولین پرداخت ساخته شود')
    if order.bill_splits.exclude(status=BillSplit.Status.CANCELLED).exists():raise ValueError('برای سفارش Split فعال وجود دارد')
    items={x.id:x for x in order.items.all()};allocated={x.id:Decimal('0') for x in items.values()};prepared=[]
    for gi,g in enumerate(groups):
        label=g.get('label') or f'نفر {gi+1}';lines=[];sub=Decimal('0')
        for row in g.get('lines',[]):
            oi=items.get(int(row['order_item']));qty=Decimal(str(row['quantity']))
            if not oi or qty<=0:raise ValueError('آیتم Split نامعتبر است')
            allocated[oi.id]+=qty
            if allocated[oi.id]>Decimal(oi.quantity):raise ValueError(f'تعداد تخصیص {oi.product_name} بیشتر از سفارش است')
            line=(Decimal(oi.unit_price)*qty).quantize(Decimal('1'));sub+=line;lines.append((oi,qty,line))
        if not lines:raise ValueError('هر Split باید حداقل یک آیتم داشته باشد')
        prepared.append((label,sub,lines))
    for oi in items.values():
        if allocated[oi.id]!=Decimal(oi.quantity):raise ValueError(f'همه تعداد {oi.product_name} باید بین Splitها تخصیص یابد')
    weights=[x[1] for x in prepared]
    discounts=_allocate_component(order.discount_total,weights);services=_allocate_component(order.service_charge_total,weights);taxes=_allocate_component(order.tax_total,weights);totals=_allocate_component(order.grand_total,weights)
    made=[]
    for i,(label,sub,lines) in enumerate(prepared):
        split=BillSplit.objects.create(order=order,label=label,items_subtotal=sub,discount_share=discounts[i],service_charge_share=services[i],tax_share=taxes[i],total=totals[i])
        for oi,qty,line in lines:BillSplitLine.objects.create(split=split,order_item=oi,quantity=qty,subtotal_share=line)
        made.append(split)
    return made

@transaction.atomic
def settle_bill_split(split,*,payments,user=None):
    # Lock BillSplit itself only. `order__customer` is nullable and PostgreSQL rejects
    # FOR UPDATE on the nullable side of that outer join. The Order row is locked separately.
    split=BillSplit.objects.select_for_update(of=('self',)).select_related('order__customer').get(pk=split.pk);order=Order.objects.select_for_update().get(pk=split.order_id)
    existing=Decimal(split.payments.filter(status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED,Payment.Status.REFUNDED]).aggregate(v=Sum('amount'))['v'] or 0)
    remaining=max(Decimal('0'),Decimal(split.total)-existing);rows=[];new_total=Decimal('0')
    for row in payments or []:
        amount=Decimal(str(row.get('amount',0)));method=row.get('method');tendered=Decimal(str(row.get('tendered_amount',amount)))
        if amount<=0 or method not in dict(Payment.Method.choices):raise ValueError('Payment نامعتبر است')
        if method==Payment.Method.CASH and tendered<amount:raise ValueError('وجه نقد دریافتی کافی نیست')
        rows.append((amount,method,tendered,tendered-amount if method==Payment.Method.CASH else Decimal('0'),row.get('reference_number',''),row.get('payer_label',split.label),row.get('gift_card_code',''),row.get('bank_account')));new_total+=amount
    if new_total!=remaining:raise ValueError(f'جمع پرداخت Split باید دقیقاً {remaining} باشد')
    made=[]
    for amount,method,tendered,change,ref,label,gift_code,bank_account_id in rows:
        gift_card=None
        bank_account=resolve_bank_account(order,account_id=bank_account_id,method=method)
        if method==Payment.Method.WALLET:
            if not order.customer_id:raise ValueError('پرداخت کیف پول نیازمند مشتری است')
            from apps.loyalty.services import debit_wallet;debit_wallet(order.customer,amount,order=order,reference=f'Split {split.label}')
        elif method==Payment.Method.GIFT_CARD:
            if not gift_code:raise ValueError('کد کارت هدیه لازم است')
            from apps.giftcards.services import debit_card;gift_card=debit_card(branch=order.branch,code=gift_code,amount=amount,order=order)
        p=Payment.objects.create(order=order,bill_split=split,amount=amount,method=method,status=Payment.Status.SUCCEEDED,reference_number=ref,payer_label=label,tendered_amount=tendered,change_amount=change,gift_card=gift_card,bank_account=bank_account,received_by=user)
        if method==Payment.Method.CASH:record_cash_movement(branch=order.branch,movement_type=CashMovement.Type.SALE,amount=amount,user=user,payment=p,note=f'Split {split.label} سفارش #{order.order_number}',reference_type='Order',reference_id=order.id)
        made.append(p)
    split.status=BillSplit.Status.PAID;split.save(update_fields=['status','updated_at'])
    total=successful_paid_amount(order);order.payment_status=Order.PaymentStatus.PAID if total>=Decimal(order.grand_total) else Order.PaymentStatus.PARTIAL;order.save(update_fields=['payment_status','updated_at'])
    return made

from decimal import Decimal
import hashlib, json
from django.db import transaction
from django.db.models import Max, Sum
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, Refund
from apps.kitchen.models import KitchenTicket
from apps.inventory.services import consume_order_inventory, restore_order_inventory
from apps.cashier.models import CashMovement
from apps.cashier.services import record_cash_movement

@transaction.atomic
def checkout_order(*, branch, items, order_type, payment_method=None, payments=None, user=None, table_session=None, customer=None, notes="", discount_code=None, manual_discount=None, manager_approved_by=None, idempotency_key=None, defer_payment=False, hold_fulfillment=False, delivery_fee=0):
    from apps.discounts.services import find_best_discount
    # Serialize numbering/checkouts per branch and make client retries safe.
    branch=branch.__class__.objects.select_for_update().get(pk=branch.pk)
    fingerprint_payload={
        'order_type':order_type,
        'items':[{'product':x['product'].id,'quantity':str(x.get('quantity',1)),'notes':x.get('notes','')} for x in items],
        'payments':payments,
        'payment_method':payment_method,
        'discount_code':discount_code,
        'manual_discount':manual_discount,
        'table_session':getattr(table_session,'id',None),
        'customer':getattr(customer,'id',None),
        'defer_payment':bool(defer_payment),
        'hold_fulfillment':bool(hold_fulfillment),
        'delivery_fee':str(delivery_fee or 0),
    }
    fingerprint=hashlib.sha256(json.dumps(fingerprint_payload,sort_keys=True,default=str,ensure_ascii=False).encode('utf-8')).hexdigest()
    if idempotency_key:
        existing=Order.objects.filter(branch=branch,idempotency_key=idempotency_key).first()
        if existing:
            if existing.idempotency_fingerprint and existing.idempotency_fingerprint!=fingerprint:
                raise ValueError('Idempotency-Key قبلاً با Payload متفاوت استفاده شده است')
            return existing
    next_no=(Order.objects.filter(branch=branch).aggregate(m=Max("order_number"))["m"] or 0)+1
    prepared=[];subtotal=Decimal("0");stations=set()
    for row in items:
        product=row["product"]
        if product.branch_id!=branch.id: raise ValueError("محصول متعلق به این شعبه نیست")
        if not product.is_available: raise ValueError(f"محصول {product.name} غیرفعال است")
        qty=Decimal(str(row.get("quantity",1)))
        if qty<=0: raise ValueError("تعداد باید بیشتر از صفر باشد")
        total=Decimal(product.price)*qty
        unit_cost=(Decimal(product.stock_item.average_cost) if product.stock_item_id else sum((Decimal(r.quantity)*Decimal(r.inventory_item.average_cost) for r in product.recipe_items.select_related('inventory_item').all()),Decimal('0')))
        prepared.append({"product":product,"quantity":qty,"line_total":total,"unit_cost":unit_cost,"notes":row.get("notes","")})
        subtotal+=total
        if product.preparation_station_id: stations.add(product.preparation_station_id)
    if not prepared: raise ValueError("سفارش خالی است")

    discount=Decimal("0"); discount_rule=None; discount_reason=""
    if manual_discount:
        amount=Decimal(str(manual_discount.get("amount") or 0))
        percent=Decimal(str(manual_discount.get("percent") or 0))
        if amount<0 or percent<0 or percent>100: raise ValueError("تخفیف دستی نامعتبر است")
        discount=amount if amount else subtotal*percent/Decimal("100")
        discount=min(discount,subtotal)
        discount_reason=manual_discount.get("reason") or "Manual manager override"
    else:
        discount_rule,discount=find_best_discount(
            branch=branch,subtotal=subtotal,lines=prepared,code=discount_code,
            allow_manager_rules=bool(manager_approved_by),
        )
        if discount_code and not discount_rule: raise ValueError("کد تخفیف معتبر یا مجاز نیست")
        if discount_rule: discount_reason=discount_rule.name

    from apps.accounting.pricing import calculate_fiscal_totals
    fiscal=calculate_fiscal_totals(branch=branch,order_type=order_type,subtotal=subtotal,discount=discount,delivery_fee=delivery_fee)
    order=Order.objects.create(
        branch=branch,order_number=next_no,order_type=order_type,customer=customer,
        table_session=table_session,notes=notes,idempotency_key=idempotency_key,idempotency_fingerprint=fingerprint,created_by=user,subtotal=subtotal,
        discount_total=discount,tax_total=fiscal['tax_total'],service_charge_total=fiscal['service_charge_total'],delivery_fee_total=fiscal['delivery_fee_total'],
        grand_total=fiscal['grand_total'],discount_rule=discount_rule,discount_reason=discount_reason,
    )
    for row in prepared:
        OrderItem.objects.create(
            order=order,product=row["product"],product_name=row["product"].name,
            quantity=row["quantity"],unit_price=row["product"].price,unit_cost_snapshot=row["unit_cost"],line_total=row["line_total"],
            notes=row["notes"],
        )
    if not defer_payment:
        from apps.payments.services import settle_order
        tender_rows=payments
        if tender_rows is None:tender_rows=[{'method':payment_method or Payment.Method.POS,'amount':order.grand_total}]
        settle_order(order,payments=tender_rows,user=user,require_full=True)
        # settle_order locks and reloads its own instance; return a current order
        # object so API callers never receive a stale unpaid payment state.
        order.refresh_from_db()
    if not hold_fulfillment:
        order.status=Order.Status.CONFIRMED
        order.save(update_fields=["status","updated_at"])
        for station_id in stations:KitchenTicket.objects.get_or_create(order=order,station_id=station_id)
        consume_order_inventory(order)
    if discount>0:
        from apps.audit.services import log_action
        log_action(actor=user,branch=branch,action='DISCOUNT_APPLIED',entity=order,description=discount_reason,after={"discount":str(discount),"manager_id":getattr(manager_approved_by,"id",None)})
    return order
@transaction.atomic
def void_order(order, *, user=None, reason='لغو سفارش'):
    order=Order.objects.select_for_update().get(pk=order.pk)
    if order.status==Order.Status.CANCELLED: return order
    if order.status==Order.Status.COMPLETED: raise ValueError('برای سفارش تکمیل‌شده از Refund استفاده کنید')
    restore_order_inventory(order,reason=reason)
    order.kitchen_tickets.update(status=KitchenTicket.Status.DONE)
    had_payment=False
    for payment in order.payments.filter(status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED]):
        had_payment=True
        refunded=payment.refunds.aggregate(v=Sum('amount'))['v'] or 0
        remain=Decimal(payment.amount)-Decimal(refunded)
        if remain>0:
            external_ref=''
            if payment.method==Payment.Method.ONLINE:
                from apps.payment_gateway.services import refund_gateway_payment
                external_ref=refund_gateway_payment(payment,remain)
            Refund.objects.create(payment=payment,amount=remain,reason=reason,method=payment.method,reference_number=external_ref,created_by=user)
            if payment.method==Payment.Method.WALLET and order.customer_id:
                from apps.loyalty.services import credit_wallet
                credit_wallet(order.customer,remain,order=order,reference=f'Void #{order.order_number}',refund=True,note=reason)
            if payment.method==Payment.Method.GIFT_CARD and payment.gift_card_id:
                from apps.giftcards.services import refund_card
                refund_card(card=payment.gift_card,amount=remain,order=order,reference=f'Void #{order.order_number}')
            if payment.method=='CASH':
                record_cash_movement(branch=order.branch,movement_type=CashMovement.Type.REFUND,amount=remain,user=user,payment=payment,note=f'Void سفارش #{order.order_number}',reference_type='Order',reference_id=order.id)
        payment.status=Payment.Status.REFUNDED; payment.save(update_fields=['status','updated_at'])
    order.status=Order.Status.CANCELLED;order.payment_status=Order.PaymentStatus.REFUNDED if had_payment else Order.PaymentStatus.UNPAID
    order.save(update_fields=['status','payment_status','updated_at'])
    from apps.audit.services import log_action
    log_action(actor=user,branch=order.branch,action='ORDER_VOID',entity=order,description=reason,after={'status':order.status,'payment_status':order.payment_status})
    return order


@transaction.atomic
def refund_order(order, *, amount, user=None, reason='برگشت وجه', method=None):
    order=Order.objects.select_for_update().get(pk=order.pk)
    requested=Decimal(str(amount))
    if requested<=0: raise ValueError('مبلغ برگشت نامعتبر است')
    refundable=[]
    total_available=Decimal('0')
    for payment in order.payments.filter(status__in=[Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED]).order_by('-created_at'):
        refunded=Decimal(payment.refunds.aggregate(v=Sum('amount'))['v'] or 0)
        remain=Decimal(payment.amount)-refunded
        if remain>0:
            refundable.append((payment,remain))
            total_available+=remain
    if requested>total_available: raise ValueError('مبلغ برگشت بیشتر از مانده قابل Refund سفارش است')

    remaining=requested; created=[]
    for payment,available in refundable:
        if remaining<=0: break
        part=min(remaining,available)
        payout_method=method or payment.method
        external_ref=''
        if payout_method==Payment.Method.ONLINE:
            from apps.payment_gateway.services import refund_gateway_payment
            external_ref=refund_gateway_payment(payment,part)
        refund=Refund.objects.create(payment=payment,amount=part,reason=reason,method=payout_method,reference_number=external_ref,created_by=user)
        if payout_method==Payment.Method.WALLET:
            if not order.customer_id:raise ValueError('Refund کیف پول نیازمند مشتری است')
            from apps.loyalty.services import credit_wallet;credit_wallet(order.customer,part,order=order,reference=f'Refund #{order.order_number}',refund=True,note=reason)
        if payout_method==Payment.Method.GIFT_CARD:
            if not payment.gift_card_id:raise ValueError('Payment به کارت هدیه متصل نیست')
            from apps.giftcards.services import refund_card;refund_card(card=payment.gift_card,amount=part,order=order,reference=f'Refund #{order.order_number}')
        if payout_method==Payment.Method.CASH:
            record_cash_movement(branch=order.branch,movement_type=CashMovement.Type.REFUND,amount=part,user=user,payment=payment,note=f'Refund سفارش #{order.order_number}',reference_type='Refund',reference_id=refund.id)
        payment_refunded=Decimal(payment.refunds.aggregate(v=Sum('amount'))['v'] or 0)
        payment.status=Payment.Status.REFUNDED if payment_refunded>=Decimal(payment.amount) else Payment.Status.PARTIALLY_REFUNDED
        payment.save(update_fields=['status','updated_at'])
        if payment.bill_split_id:
            from apps.payments.models import BillSplit
            split=BillSplit.objects.select_for_update().get(pk=payment.bill_split_id)
            split_paid=Decimal(split.payments.aggregate(v=Sum('amount'))['v'] or 0)-Decimal(Refund.objects.filter(payment__bill_split=split).aggregate(v=Sum('amount'))['v'] or 0)
            split.status=BillSplit.Status.OPEN if split_paid<=0 else (BillSplit.Status.PARTIAL if split_paid<Decimal(split.total) else BillSplit.Status.PAID)
            split.save(update_fields=['status','updated_at'])
        created.append(refund);remaining-=part

    order_refunded=Decimal(Refund.objects.filter(payment__order=order).aggregate(v=Sum('amount'))['v'] or 0)
    order.payment_status=Order.PaymentStatus.REFUNDED if order_refunded>=Decimal(order.grand_total) else Order.PaymentStatus.PARTIALLY_REFUNDED
    order.save(update_fields=['payment_status','updated_at'])
    from apps.audit.services import log_action
    log_action(actor=user,branch=order.branch,action='ORDER_REFUND',entity=order,description=reason,after={'amount':str(requested),'refund_count':len(created)})
    return created

@transaction.atomic
def apply_discount(order, *, amount=0, percent=0, user=None, reason=''):
    from apps.audit.services import log_action
    order=Order.objects.select_for_update().get(pk=order.pk)
    if order.payment_status!=Order.PaymentStatus.UNPAID:
        raise ValueError('پس از پرداخت، مبلغ سفارش با Discount تغییر نمی‌کند؛ از Refund استفاده کنید')
    amount=Decimal(str(amount or 0)); percent=Decimal(str(percent or 0))
    if amount<0 or percent<0 or percent>100: raise ValueError('تخفیف نامعتبر است')
    discount=amount if amount else (Decimal(order.subtotal)*percent/Decimal('100'))
    discount=min(discount,Decimal(order.subtotal))
    from apps.accounting.pricing import calculate_fiscal_totals
    before={'discount_total':str(order.discount_total),'grand_total':str(order.grand_total)}
    fiscal=calculate_fiscal_totals(branch=order.branch,order_type=order.order_type,subtotal=order.subtotal,discount=discount,delivery_fee=order.delivery_fee_total)
    order.discount_total=discount;order.tax_total=fiscal['tax_total'];order.service_charge_total=fiscal['service_charge_total'];order.delivery_fee_total=fiscal['delivery_fee_total'];order.grand_total=fiscal['grand_total']
    order.save(update_fields=['discount_total','tax_total','service_charge_total','delivery_fee_total','grand_total','updated_at'])
    log_action(actor=user,branch=order.branch,action='ORDER_DISCOUNT',entity=order,description=reason,before=before,after={'discount_total':str(discount),'grand_total':str(order.grand_total)})
    return order

@transaction.atomic
def release_held_order(order):
    order=Order.objects.select_for_update().prefetch_related('items__product__preparation_station').get(pk=order.pk)
    if order.status!=Order.Status.DRAFT:return order
    stations={x.product.preparation_station_id for x in order.items.all() if x.product.preparation_station_id}
    consume_order_inventory(order)
    for station_id in stations:KitchenTicket.objects.get_or_create(order=order,station_id=station_id)
    order.status=Order.Status.CONFIRMED;order.save(update_fields=['status','updated_at'])
    return order

@transaction.atomic
def transfer_order_items(*,source_order,destination_order,lines,user=None):
    from apps.accounting.pricing import calculate_fiscal_totals
    from apps.audit.services import log_action
    # Do not prefetch items here: the transfer mutates these rows and totals
    # must be calculated from a fresh database query, not a relation cache.
    a=Order.objects.select_for_update().get(pk=source_order.pk)
    b=Order.objects.select_for_update().get(pk=destination_order.pk)
    if a.id==b.id or a.branch_id!=b.branch_id:raise ValueError('دو سفارش معتبر در یک شعبه لازم است')
    if a.payment_status!=Order.PaymentStatus.UNPAID or b.payment_status!=Order.PaymentStatus.UNPAID:raise ValueError('انتقال آیتم فقط قبل از پرداخت مجاز است')
    if a.status in [Order.Status.CANCELLED,Order.Status.COMPLETED] or b.status in [Order.Status.CANCELLED,Order.Status.COMPLETED]:raise ValueError('وضعیت سفارش قابل انتقال نیست')
    for row in lines:
        oi=OrderItem.objects.select_for_update().get(pk=row['order_item'],order=a)
        qty=Decimal(str(row['quantity']))
        if qty<=0 or qty>Decimal(oi.quantity):raise ValueError('تعداد انتقال نامعتبر است')
        if oi.status!=OrderItem.Status.NEW:raise ValueError(f'{oi.product_name} وارد آماده‌سازی شده و قابل انتقال نیست')
        if qty==Decimal(oi.quantity):
            oi.order=b;oi.save(update_fields=['order','updated_at'])
        else:
            oi.quantity=Decimal(oi.quantity)-qty;oi.line_total=Decimal(oi.unit_price)*Decimal(oi.quantity);oi.save(update_fields=['quantity','line_total','updated_at'])
            OrderItem.objects.create(order=b,product=oi.product,product_name=oi.product_name,quantity=qty,unit_price=oi.unit_price,unit_cost_snapshot=oi.unit_cost_snapshot,line_total=Decimal(oi.unit_price)*qty,status=oi.status,notes=oi.notes)
    for order in [a,b]:
        sub=sum((Decimal(x.line_total) for x in order.items.all()),Decimal('0'))
        # Existing order-level discount is dropped to avoid unsafe allocation after moving items.
        fiscal=calculate_fiscal_totals(branch=order.branch,order_type=order.order_type,subtotal=sub,discount=0,delivery_fee=order.delivery_fee_total)
        order.subtotal=sub;order.discount_total=0;order.discount_rule=None;order.discount_reason='';order.tax_total=fiscal['tax_total'];order.service_charge_total=fiscal['service_charge_total'];order.delivery_fee_total=fiscal['delivery_fee_total'];order.grand_total=fiscal['grand_total']
        order.save(update_fields=['subtotal','discount_total','discount_rule','discount_reason','tax_total','service_charge_total','delivery_fee_total','grand_total','updated_at'])
        stations=set(order.items.exclude(product__preparation_station__isnull=True).values_list('product__preparation_station_id',flat=True))
        for station in stations:KitchenTicket.objects.get_or_create(order=order,station_id=station)
    log_action(actor=user,branch=a.branch,action='ORDER_ITEMS_TRANSFERRED',entity=a,after={'destination_order':b.id,'lines':lines})
    return a,b

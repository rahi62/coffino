from decimal import Decimal
from django.db import transaction
from django.utils.text import slugify
from apps.catalog.models import Product
from apps.customers.models import Customer
from apps.dining.models import Table,TableSession
from apps.orders.models import Order
from apps.orders.services import checkout_order,release_held_order
from apps.payments.models import Payment
from .models import OnlineMenuSettings,TableQrToken,OnlineOrder

@transaction.atomic
def ensure_settings(branch):
    slug=slugify(f'{branch.business.name}-{branch.name}',allow_unicode=False) or f'branch-{branch.id}'
    base=slug;idx=1
    while OnlineMenuSettings.objects.filter(public_slug=slug).exclude(branch=branch).exists():idx+=1;slug=f'{base}-{idx}'
    obj,_=OnlineMenuSettings.objects.get_or_create(branch=branch,defaults={'public_slug':slug})
    return obj

def public_menu(settings,table_token=None):
    table=None
    if table_token:
        try:table=TableQrToken.objects.select_related('table__hall__branch').get(token=table_token,is_active=True,table__hall__branch=settings.branch).table
        except TableQrToken.DoesNotExist:table=None
    products=Product.objects.filter(branch=settings.branch,is_available=True).select_related('category').order_by('category__sort_order','category__name','name')
    return {'branch':settings.branch,'settings':settings,'table':table,'products':products}

@transaction.atomic
def create_public_order(*,settings,items,customer_name='',customer_phone='',order_type='TAKEAWAY',table_token=None,idempotency_key=None,delivery=None):
    if not settings.is_enabled or not settings.accepting_orders:raise ValueError('سفارش آنلاین این شعبه فعال نیست')
    allowed=[]
    if settings.allow_takeaway:allowed.append(Order.Type.TAKEAWAY)
    if settings.allow_pickup:allowed.append(Order.Type.PICKUP)
    if settings.allow_dine_in_qr:allowed.append(Order.Type.DINE_IN)
    if settings.allow_delivery:allowed.append(Order.Type.DELIVERY)
    if order_type not in allowed:raise ValueError('نوع سفارش آنلاین مجاز نیست')
    customer=None
    if customer_phone:
        customer,_=Customer.objects.get_or_create(branch=settings.branch,phone=customer_phone,defaults={'name':customer_name or customer_phone,'is_walk_in':False})
        if customer_name and customer.name!=customer_name:customer.name=customer_name;customer.save(update_fields=['name','updated_at'])
    rows=[]
    subtotal=Decimal('0')
    for row in items:
        product=Product.objects.get(pk=row['product'],branch=settings.branch,is_available=True)
        qty=Decimal(str(row.get('quantity',1)))
        if qty<=0:raise ValueError('تعداد نامعتبر است')
        rows.append({'product':product,'quantity':qty,'notes':row.get('notes','')});subtotal+=Decimal(product.price)*qty
    table_session=None;qr=None;address=None;delivery_fee=Decimal('0')
    if order_type==Order.Type.DINE_IN:
        if not table_token:raise ValueError('QR میز لازم است')
        qr=TableQrToken.objects.select_for_update().select_related('table__hall__branch').get(token=table_token,is_active=True,table__hall__branch=settings.branch)
        table=Table.objects.select_for_update().get(pk=qr.table_id);table_session=table.sessions.filter(is_open=True).first()
        if not table_session:
            table_session=TableSession.objects.create(table=table,customer_count=1);table.status=Table.Status.OCCUPIED;table.save(update_fields=['status','updated_at'])
    elif order_type==Order.Type.DELIVERY:
        from apps.delivery.models import DeliveryZone,DeliveryAddress
        from apps.delivery.services import delivery_quote
        delivery=delivery or {};zone=DeliveryZone.objects.get(branch=settings.branch,code=delivery.get('zone_code'),is_active=True)
        delivery_fee=delivery_quote(zone,subtotal)
        if not delivery.get('address') or not delivery.get('phone',customer_phone):raise ValueError('آدرس و تلفن ارسال لازم است')
        address=DeliveryAddress.objects.create(
            customer=customer,branch=settings.branch,zone=zone,recipient_name=delivery.get('recipient_name') or customer_name or customer_phone,
            phone=delivery.get('phone') or customer_phone,address=delivery.get('address'),postal_code=delivery.get('postal_code',''),
            latitude=delivery.get('latitude') or None,longitude=delivery.get('longitude') or None,notes=delivery.get('notes','')
        )
    hold=settings.payment_mode==OnlineMenuSettings.PaymentMode.ONLINE
    order=checkout_order(branch=settings.branch,items=rows,order_type=order_type,user=None,table_session=table_session,customer=customer,notes='Online Order',idempotency_key=idempotency_key,defer_payment=True,hold_fulfillment=hold,delivery_fee=delivery_fee)
    if Decimal(order.subtotal)<Decimal(settings.min_order_amount):raise ValueError('مبلغ اقلام سفارش کمتر از حداقل سفارش آنلاین است')
    online,_=OnlineOrder.objects.get_or_create(order=order,defaults={'branch':settings.branch,'table_token':qr,'customer_name':customer_name,'customer_phone':customer_phone,'payment_mode':settings.payment_mode,'estimated_minutes':settings.estimated_minutes+(address.zone.estimated_minutes if address and address.zone else 0),'status':OnlineOrder.Status.PAYMENT_PENDING if hold else OnlineOrder.Status.RECEIVED,'delivery_address':address})
    if order_type==Order.Type.DELIVERY and address:
        from apps.delivery.services import create_delivery_assignment
        create_delivery_assignment(order=order,address=address,fee=delivery_fee)
    if hold and not order.payments.filter(method=Payment.Method.ONLINE,status=Payment.Status.PENDING).exists():
        Payment.objects.create(order=order,amount=order.grand_total,method=Payment.Method.ONLINE,status=Payment.Status.PENDING,payer_label=customer_name)
    return online
@transaction.atomic
def confirm_online_payment(online_order,reference=''):
    x=OnlineOrder.objects.select_for_update().select_related('order').get(pk=online_order.pk);order=Order.objects.select_for_update().get(pk=x.order_id)
    p=order.payments.filter(method=Payment.Method.ONLINE,status=Payment.Status.PENDING).first()
    if not p:raise ValueError('Payment Intent در انتظار وجود ندارد')
    p.status=Payment.Status.SUCCEEDED;p.reference_number=reference;p.save(update_fields=['status','reference_number','updated_at'])
    order.payment_status=Order.PaymentStatus.PAID;order.save(update_fields=['payment_status','updated_at']);release_held_order(order)
    x.status=OnlineOrder.Status.RECEIVED;x.save(update_fields=['status','updated_at'])
    from apps.audit.services import log_action;log_action(branch=x.branch,action='ONLINE_PAYMENT_CONFIRMED',entity=x,description=reference,after={'order':order.id,'amount':str(order.grand_total)})
    return x

import logging

from .shared import *
from .shared import BaseVS, _branch_accessible

logger=logging.getLogger(__name__)


def _public_error(message,code="invalid_request",status_code=400):
    return Response(
        {"detail":message,"error":{"code":code,"message":message}},
        status=status_code
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@throttle_classes([PublicMenuThrottle])
def public_table_qr_svg(request,token):
    import io
    import qrcode
    import qrcode.image.svg

    qr=get_object_or_404(
        TableQrToken.objects.select_related('table__hall__branch'),
        token=token,is_active=True
    )
    settings=get_object_or_404(
        OnlineMenuSettings,branch=qr.table.hall.branch,is_enabled=True
    )
    base=(settings.public_base_url or 'http://127.0.0.1:3000').rstrip('/')
    url=f'{base}/menu/{settings.public_slug}?table={qr.token}'
    img=qrcode.make(url,image_factory=qrcode.image.svg.SvgPathImage)
    buf=io.BytesIO()
    img.save(buf)
    return HttpResponse(buf.getvalue(),content_type='image/svg+xml')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@throttle_classes([PublicMenuThrottle])
def public_push_key(request,slug):
    settings=get_object_or_404(OnlineMenuSettings,public_slug=slug,is_enabled=True)
    try:
        cfg=settings.branch.push_provider
    except PushProviderConfig.DoesNotExist:
        return Response({'enabled':False,'public_key':''})
    return Response({
        'enabled':bool(cfg.is_active and cfg.vapid_public_key),
        'public_key':cfg.vapid_public_key if cfg.is_active else ''
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([OnlineOrderThrottle])
def public_push_subscribe(request,token):
    online=get_object_or_404(
        OnlineOrder.objects.select_related('order__customer','branch'),
        access_token=token
    )
    data=request.data.get('subscription') or request.data
    keys=data.get('keys') or {}
    endpoint=str(data.get('endpoint') or '')
    p256dh=str(keys.get('p256dh') or '')
    auth=str(keys.get('auth') or '')
    if not endpoint or not p256dh or not auth:
        return _public_error('Push subscription ناقص است','invalid_push_subscription')
    if len(endpoint)>4096 or len(p256dh)>1024 or len(auth)>512:
        return _public_error('Push subscription نامعتبر است','invalid_push_subscription')

    sub,_=PushSubscription.objects.update_or_create(
        branch=online.branch,endpoint=endpoint,
        defaults={
            'customer':online.order.customer,'order':online.order,
            'p256dh':p256dh,'auth':auth,
            'user_agent':request.META.get('HTTP_USER_AGENT','')[:250],
            'is_active':True
        }
    )
    return Response({'ok':True,'id':sub.id},status=201)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@throttle_classes([PublicMenuThrottle])
def public_menu_api(request,slug):
    settings=get_object_or_404(OnlineMenuSettings,public_slug=slug,is_enabled=True)
    data=public_menu(settings,request.query_params.get('table'))
    categories={}
    for product in data['products']:
        key=product.category.name if product.category_id else 'منو'
        categories.setdefault(key,[]).append({
            'id':product.id,'name':product.name,'price':product.price,
            'product_type':product.product_type
        })
    zones=(
        list(DeliveryZone.objects.filter(branch=settings.branch,is_active=True).values(
            'code','name','delivery_fee','min_order_amount',
            'free_delivery_above','estimated_minutes'
        ))
        if settings.allow_delivery else []
    )
    push_enabled=PushProviderConfig.objects.filter(
        branch=settings.branch,is_active=True
    ).exists()

    return Response({
        'branch':{
            'id':settings.branch.id,'name':settings.branch.name,
            'address':settings.branch.address,'phone':settings.branch.phone
        },
        'settings':{
            'welcome_text':settings.welcome_text,
            'estimated_minutes':settings.estimated_minutes,
            'payment_mode':settings.payment_mode,
            'allow_takeaway':settings.allow_takeaway,
            'allow_pickup':settings.allow_pickup,
            'allow_dine_in_qr':settings.allow_dine_in_qr,
            'allow_delivery':settings.allow_delivery,
            'push_enabled':push_enabled
        },
        'delivery_zones':zones,
        'table':(
            {'id':data['table'].id,'number':data['table'].number}
            if data['table'] else None
        ),
        'categories':[{'name':k,'products':v} for k,v in categories.items()]
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([PublicMenuThrottle])
def public_order_preview(request,slug):
    from apps.accounting.pricing import calculate_fiscal_totals

    settings=get_object_or_404(OnlineMenuSettings,public_slug=slug,is_enabled=True)
    order_type=request.data.get('order_type','TAKEAWAY')
    allowed={
        'DINE_IN':settings.allow_dine_in_qr,
        'TAKEAWAY':settings.allow_takeaway,
        'PICKUP':settings.allow_pickup,
        'DELIVERY':settings.allow_delivery
    }
    if not allowed.get(order_type,False):
        return _public_error('نوع سفارش غیرفعال است','order_type_disabled')

    subtotal=Decimal('0')
    delivery_fee=Decimal('0')
    try:
        rows=request.data.get('items',[])
        if not rows:
            raise ValueError('حداقل یک آیتم لازم است')
        for row in rows:
            product=Product.objects.get(
                pk=row.get('product'),branch=settings.branch,is_available=True
            )
            qty=Decimal(str(row.get('quantity',1)))
            if qty<=0:
                raise ValueError('تعداد نامعتبر است')
            subtotal+=Decimal(product.price)*qty
        if order_type=='DELIVERY':
            zone=DeliveryZone.objects.get(
                branch=settings.branch,code=request.data.get('zone_code'),is_active=True
            )
            delivery_fee=delivery_quote(zone,subtotal)
    except Product.DoesNotExist:
        return _public_error('یکی از محصولات معتبر یا قابل سفارش نیست','invalid_product')
    except DeliveryZone.DoesNotExist:
        return _public_error('منطقه ارسال معتبر نیست','invalid_delivery_zone')
    except (ValueError,TypeError) as exc:
        return _public_error(str(exc),'invalid_order')

    fiscal=calculate_fiscal_totals(
        branch=settings.branch,order_type=order_type,subtotal=subtotal,
        discount=0,delivery_fee=delivery_fee
    )
    return Response({'subtotal':subtotal,'discount_total':0,**fiscal})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([OnlineOrderThrottle])
@transaction.atomic
def public_order_create(request,slug):
    settings=get_object_or_404(OnlineMenuSettings,public_slug=slug,is_enabled=True)
    try:
        online=create_public_order(
            settings=settings,items=request.data.get('items',[]),
            customer_name=request.data.get('customer_name',''),
            customer_phone=request.data.get('customer_phone',''),
            order_type=request.data.get('order_type','TAKEAWAY'),
            table_token=request.data.get('table_token'),
            idempotency_key=(
                request.headers.get('Idempotency-Key') or
                request.data.get('idempotency_key')
            ),
            delivery=request.data.get('delivery')
        )
    except Product.DoesNotExist:
        transaction.set_rollback(True)
        return _public_error('یکی از محصولات معتبر یا قابل سفارش نیست','invalid_product')
    except TableQrToken.DoesNotExist:
        transaction.set_rollback(True)
        return _public_error('QR میز معتبر نیست','invalid_table_qr')
    except DeliveryZone.DoesNotExist:
        transaction.set_rollback(True)
        return _public_error('منطقه ارسال معتبر نیست','invalid_delivery_zone')
    except (ValueError,TypeError) as exc:
        transaction.set_rollback(True)
        return _public_error(str(exc),'invalid_order')
    except Exception:
        transaction.set_rollback(True)
        logger.exception('Unexpected public order creation failure')
        return _public_error(
            'ثبت سفارش در حال حاضر ممکن نیست. دوباره تلاش کنید.',
            'order_creation_failed',500
        )

    payment_url=''
    if online.payment_mode==OnlineMenuSettings.PaymentMode.ONLINE:
        try:
            intent=create_payment_intent(online)
            payment_url=intent.payment_url
        except Exception:
            transaction.set_rollback(True)
            logger.exception(
                'Payment intent creation failed for online_order=%s',online.pk
            )
            return _public_error(
                'شروع پرداخت آنلاین در حال حاضر ممکن نیست.',
                'payment_initialization_failed',503
            )

    return Response({
        'access_token':online.access_token,
        'online_status':online.status,
        'order_number':online.order.order_number,
        'order_status':online.order.status,
        'payment_status':online.order.payment_status,
        'grand_total':online.order.grand_total,
        'delivery_fee_total':online.order.delivery_fee_total,
        'estimated_minutes':online.estimated_minutes,
        'payment_mode':online.payment_mode,
        'payment_url':payment_url
    },status=201)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@throttle_classes([PublicMenuThrottle])
def public_order_status(request,token):
    online=get_object_or_404(
        OnlineOrder.objects.select_related('order','branch'),
        access_token=token
    )
    delivery=None
    try:
        assignment=online.order.delivery_assignment
        delivery={
            'status':assignment.status,
            'courier':assignment.courier.name if assignment.courier else None
        }
    except DeliveryAssignment.DoesNotExist:
        pass
    return Response({
        'order_number':online.order.order_number,
        'online_status':online.status,
        'order_status':online.order.status,
        'payment_status':online.order.payment_status,
        'grand_total':online.order.grand_total,
        'delivery_fee_total':online.order.delivery_fee_total,
        'estimated_minutes':online.estimated_minutes,
        'branch':online.branch.name,
        'delivery':delivery
    })


@api_view(['GET','POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([OnlineOrderThrottle])
def public_payment_callback(request,token):
    online=get_object_or_404(
        OnlineOrder.objects.select_related('branch'),access_token=token
    )
    authority=(
        request.query_params.get('Authority') or
        request.query_params.get('authority') or
        request.query_params.get('payment_id') or
        request.data.get('Authority') or
        request.data.get('authority') or
        request.data.get('payment_id') or ''
    )
    status_value=(
        request.query_params.get('Status') or
        request.query_params.get('status') or
        request.query_params.get('success') or
        request.data.get('Status') or
        request.data.get('status') or
        request.data.get('success') or ''
    )
    try:
        verify_payment(online=online,authority=authority,status=status_value)
        result='success'
    except Exception:
        logger.exception('Payment verification failed for online_order=%s',online.pk)
        result='failed'

    try:
        settings=online.branch.online_menu_settings
        base=settings.public_base_url.rstrip('/')
        slug=settings.public_slug
    except OnlineMenuSettings.DoesNotExist:
        base='http://127.0.0.1:3000'
        slug=''
    return HttpResponseRedirect(
        f'{base}/menu/{slug}?order={online.access_token}&payment={result}'
    )

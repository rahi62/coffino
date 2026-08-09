import json,urllib.request,urllib.parse
from django.db import transaction
from django.utils import timezone
from .models import PaymentGatewayConfig,GatewayIntent
from apps.payments.models import Payment
from apps.online_ordering.models import OnlineOrder
from apps.online_ordering.services import confirm_online_payment

def _post_json(url,payload,headers=None,timeout=15):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',**(headers or {})},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode() or '{}')

def _callback_url(cfg,online):
    base=cfg.callback_base_url.rstrip('/')
    return f'{base}/api/v1/public/payments/{online.access_token}/callback/' if base else ''

@transaction.atomic
def create_payment_intent(online):
    online=OnlineOrder.objects.select_for_update().select_related('order__branch').get(pk=online.pk)
    payment=online.order.payments.filter(method=Payment.Method.ONLINE,status=Payment.Status.PENDING).first()
    if not payment:raise ValueError('Online Payment در انتظار وجود ندارد')
    try:cfg=online.branch.payment_gateway
    except PaymentGatewayConfig.DoesNotExist:raise ValueError('درگاه پرداخت تنظیم نشده است')
    if not cfg.is_active:raise ValueError('درگاه پرداخت غیرفعال است')
    intent,_=GatewayIntent.objects.get_or_create(payment=payment,defaults={'provider':cfg.provider})
    if intent.status==GatewayIntent.Status.VERIFIED:return intent
    callback=_callback_url(cfg,online);amount=int(payment.amount)
    if cfg.provider==PaymentGatewayConfig.Provider.MOCK:
        authority=f'MOCK-{online.id}-{payment.id}'
        intent.authority=authority;intent.callback_url=callback
        intent.payment_url=f'{callback}?Status=OK&Authority={urllib.parse.quote(authority)}'
        intent.status=GatewayIntent.Status.REDIRECTED;intent.save()
        return intent
    if cfg.provider==PaymentGatewayConfig.Provider.ZARINPAL:
        merchant=cfg.get_merchant_id()
        if not merchant:raise ValueError('Merchant ID تنظیم نشده است')
        request_url=cfg.request_url or 'https://api.zarinpal.com/pg/v4/payment/request.json'
        gateway=cfg.gateway_url or 'https://www.zarinpal.com/pg/StartPay/'
        payload={'merchant_id':merchant,'amount':amount,'callback_url':callback,'description':f'Cafino Order #{online.order.order_number}','metadata':{'mobile':online.customer_phone or ''}}
        data=_post_json(request_url,payload,timeout=cfg.timeout_seconds)
        result=data.get('data') or {}
        if int(result.get('code',0)) not in [100,101]:raise ValueError((data.get('errors') or {}).get('message') or 'خطا در ایجاد پرداخت')
        authority=result.get('authority')
        intent.authority=authority;intent.callback_url=callback;intent.request_payload=payload;intent.payment_url=gateway+authority;intent.status=GatewayIntent.Status.REDIRECTED;intent.save()
        return intent
    # Generic HTTP. field mapping can be adjusted via `extra`.
    headers={}
    key=cfg.get_api_key()
    if key:headers['Authorization']=f'Bearer {key}'
    payload={'amount':amount,'callback_url':callback,'order_id':str(online.order.id)}
    payload.update(cfg.extra.get('request_payload',{}) if cfg.extra else {})
    data=_post_json(cfg.request_url,payload,headers,timeout=cfg.timeout_seconds)
    authority=str(data.get('authority') or data.get('payment_id') or data.get('id') or '')
    url=str(data.get('payment_url') or data.get('url') or '')
    if not authority or not url:raise ValueError('پاسخ درگاه Generic معتبر نیست')
    intent.authority=authority;intent.callback_url=callback;intent.request_payload=payload;intent.payment_url=url;intent.status=GatewayIntent.Status.REDIRECTED;intent.save()
    return intent

@transaction.atomic
def verify_payment(*,online,authority,status='OK'):
    online=OnlineOrder.objects.select_for_update().select_related('order__branch').get(pk=online.pk)
    payment=online.order.payments.filter(method=Payment.Method.ONLINE).first()
    if not payment:raise ValueError('Payment یافت نشد')
    intent=GatewayIntent.objects.select_for_update().get(payment=payment)
    if intent.status==GatewayIntent.Status.VERIFIED:return intent
    if status not in ['OK','ok','true','True','1','SUCCESS','success']:
        intent.status=GatewayIntent.Status.CANCELLED;intent.save(update_fields=['status','updated_at']);raise ValueError('پرداخت توسط کاربر لغو یا ناموفق شد')
    cfg=online.branch.payment_gateway
    if intent.authority and authority and intent.authority!=authority:raise ValueError('Authority با Payment Intent تطابق ندارد')
    if cfg.provider==PaymentGatewayConfig.Provider.MOCK:
        ref=f'MOCK-REF-{payment.id}'
    elif cfg.provider==PaymentGatewayConfig.Provider.ZARINPAL:
        payload={'merchant_id':cfg.get_merchant_id(),'amount':int(payment.amount),'authority':authority}
        data=_post_json(cfg.verify_url or 'https://api.zarinpal.com/pg/v4/payment/verify.json',payload,timeout=cfg.timeout_seconds)
        result=data.get('data') or {};code=int(result.get('code',0))
        if code not in [100,101]:raise ValueError((data.get('errors') or {}).get('message') or 'تأیید پرداخت ناموفق است')
        ref=str(result.get('ref_id') or '')
        intent.verify_payload=data
    else:
        headers={};key=cfg.get_api_key()
        if key:headers['Authorization']=f'Bearer {key}'
        payload={'authority':authority,'payment_id':authority,'amount':int(payment.amount)}
        data=_post_json(cfg.verify_url,payload,headers,timeout=cfg.timeout_seconds)
        if not bool(data.get('success',data.get('verified',False))):raise ValueError('تأیید Generic Payment ناموفق است')
        ref=str(data.get('reference_id') or data.get('ref_id') or authority);intent.verify_payload=data
    confirm_online_payment(online,reference=ref)
    intent.status=GatewayIntent.Status.VERIFIED;intent.reference_id=ref;intent.verified_at=timezone.now()
    intent.save(update_fields=['status','reference_id','verified_at','verify_payload','updated_at'])
    return intent


def refund_gateway_payment(payment,amount):
    """Perform PSP refund first. Returns provider reference. Never mutates Cafino refund ledger."""
    from decimal import Decimal
    amount=Decimal(str(amount))
    if payment.method!=Payment.Method.ONLINE:raise ValueError('Payment آنلاین نیست')
    try:cfg=payment.order.branch.payment_gateway
    except PaymentGatewayConfig.DoesNotExist:raise ValueError('تنظیمات درگاه موجود نیست')
    try:intent=payment.gateway_intent
    except GatewayIntent.DoesNotExist:raise ValueError('Gateway Intent موجود نیست')
    if intent.status!=GatewayIntent.Status.VERIFIED:raise ValueError('Payment درگاه تأییدشده نیست')
    if cfg.provider==PaymentGatewayConfig.Provider.MOCK:
        return f'MOCK-REFUND-{payment.id}-{int(amount)}'
    if not cfg.refund_url:
        raise ValueError('Refund API این PSP در Cafino تنظیم نشده است؛ برگشت وجه خارجی بدون تأیید PSP ثبت نمی‌شود')
    headers={}
    key=cfg.get_api_key()
    if key:headers['Authorization']=f'Bearer {key}'
    payload={
        'authority':intent.authority,'reference_id':intent.reference_id,
        'payment_id':intent.authority,'amount':int(amount),
        'merchant_id':cfg.get_merchant_id() or '',
    }
    if cfg.extra:payload.update(cfg.extra.get('refund_payload',{}))
    data=_post_json(cfg.refund_url,payload,headers,timeout=cfg.timeout_seconds)
    if not bool(data.get('success',data.get('refunded',False))):
        code=data.get('code')
        if code not in [100,101,'100','101']:raise ValueError('PSP Refund تأیید نشد')
    return str(data.get('reference_id') or data.get('ref_id') or data.get('refund_id') or intent.reference_id)

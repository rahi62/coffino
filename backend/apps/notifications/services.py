import json,urllib.request,urllib.error
from datetime import timedelta
from django.db import transaction, models
from django.utils import timezone
from .models import Notification,SmsProviderConfig

def order_phone(order):
    if order.customer_id and order.customer.phone:return order.customer.phone
    try:return order.takeaway_profile.customer_phone
    except Exception:return ''

@transaction.atomic
def enqueue_order_ready(order):
    title=f'سفارش #{order.order_number} آماده است'
    body=f'سفارش شما در {order.branch.name} آماده تحویل است.'
    Notification.objects.get_or_create(branch=order.branch,order=order,channel=Notification.Channel.IN_APP,event='ORDER_READY',dedupe_key=f'order-ready-inapp-{order.id}',defaults={'customer':order.customer,'title':title,'body':body,'status':Notification.Status.SENT,'sent_at':timezone.now()})
    phone=order_phone(order)
    if phone:
        Notification.objects.get_or_create(branch=order.branch,order=order,channel=Notification.Channel.SMS,event='ORDER_READY',dedupe_key=f'order-ready-sms-{order.id}',defaults={'customer':order.customer,'recipient':phone,'title':title,'body':body})
    from .models import PushSubscription
    subs=PushSubscription.objects.filter(branch=order.branch,is_active=True).filter(models.Q(order=order)|models.Q(customer=order.customer) if order.customer_id else models.Q(order=order))
    for sub in subs:
        Notification.objects.get_or_create(branch=order.branch,order=order,channel=Notification.Channel.PUSH,event='ORDER_READY',recipient=str(sub.id),dedupe_key=f'order-ready-push-{order.id}-{sub.id}',defaults={'customer':order.customer,'title':title,'body':body})

def _send_sms(n):
    try:cfg=n.branch.sms_provider
    except SmsProviderConfig.DoesNotExist:raise ValueError('SMS provider تنظیم نشده است')
    if not cfg.is_active or not cfg.endpoint_url:raise ValueError('SMS provider غیرفعال است')
    payload={cfg.phone_field:n.recipient,cfg.message_field:n.body}
    if cfg.sender:payload[cfg.sender_field]=cfg.sender
    headers={'Content-Type':'application/json'}
    for k,v in (cfg.headers or {}).items():headers[str(k)]=str(v).replace('{api_key}',cfg.api_key)
    req=urllib.request.Request(cfg.endpoint_url,data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers=headers,method='POST')
    with urllib.request.urlopen(req,timeout=cfg.timeout_seconds) as response:
        code=getattr(response,'status',200)
        if code<200 or code>=300:raise ValueError(f'SMS HTTP {code}')
    return True


def _send_push(n):
    from .models import PushSubscription,PushProviderConfig
    try:sub=PushSubscription.objects.get(pk=int(n.recipient),is_active=True)
    except (PushSubscription.DoesNotExist,ValueError):raise ValueError('Push subscription معتبر نیست')
    try:cfg=n.branch.push_provider
    except PushProviderConfig.DoesNotExist:raise ValueError('Push provider تنظیم نشده است')
    if not cfg.is_active or not cfg.vapid_public_key or not cfg.get_private_key():raise ValueError('Push provider غیرفعال است')
    try:
        from pywebpush import webpush,WebPushException
    except ImportError:raise ValueError('pywebpush نصب نشده است')
    payload=json.dumps({'title':n.title,'body':n.body,'event':n.event,'order_id':n.order_id},ensure_ascii=False)
    try:
        webpush(subscription_info={'endpoint':sub.endpoint,'keys':{'p256dh':sub.p256dh,'auth':sub.auth}},data=payload,vapid_private_key=cfg.get_private_key(),vapid_claims={'sub':cfg.subject})
    except Exception as e:
        if '410' in str(e) or '404' in str(e):
            sub.is_active=False;sub.save(update_fields=['is_active','updated_at'])
        raise

@transaction.atomic
def process_notification(notification):
    n=Notification.objects.select_for_update().select_related('branch').get(pk=notification.pk)
    if n.status==Notification.Status.SENT:return n
    n.status=Notification.Status.PROCESSING;n.attempts+=1;n.save(update_fields=['status','attempts','updated_at'])
    try:
        if n.channel==Notification.Channel.IN_APP:
            pass
        elif n.channel==Notification.Channel.SMS:
            _send_sms(n)
        elif n.channel==Notification.Channel.PUSH:
            _send_push(n)
        n.status=Notification.Status.SENT;n.sent_at=timezone.now();n.last_error='';n.next_attempt_at=None
        if n.event=='ORDER_READY' and n.order_id:
            try:
                profile=n.order.takeaway_profile;profile.notified_at=n.sent_at;profile.save(update_fields=['notified_at','updated_at'])
            except Exception:pass
    except Exception as e:
        n.status=Notification.Status.FAILED;n.last_error=str(e)[:2000]
        delay=min(60,2**min(n.attempts,6));n.next_attempt_at=timezone.now()+timedelta(minutes=delay)
    n.save(update_fields=['status','sent_at','last_error','next_attempt_at','updated_at'])
    return n

def process_pending(branch=None,business=None,limit=50,allow_global=False):
    qs=Notification.objects.filter(
        status__in=[Notification.Status.PENDING,Notification.Status.FAILED]
    ).filter(
        models.Q(next_attempt_at__isnull=True)|models.Q(next_attempt_at__lte=timezone.now())
    ).order_by('created_at')
    if branch is not None:
        qs=qs.filter(branch=branch)
    elif business is not None:
        qs=qs.filter(branch__business=business)
    elif not allow_global:
        # Global processing is intentionally reserved for internal worker code.
        qs=qs.none()
    done=[]
    for n in qs[:limit]:
        done.append(process_notification(n))
    return done

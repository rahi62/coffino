import json
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone

from apps.core.network_safety import post_json, validate_http_target
from .models import Notification, PagerProviderConfig, SmsProviderConfig


def _queue_delivery(notification):
    """Hand delivery to Celery after the surrounding order transaction commits."""
    from .tasks import deliver_notification
    def dispatch():
        try:
            deliver_notification.delay(notification.pk)
        except Exception:
            # The persisted notification remains pending for the worker/beat retry path.
            pass
    transaction.on_commit(dispatch)


def _ready_copy(order):
    title=f'سفارش #{order.order_number} آماده است'
    return title, f'سفارش شما در {order.branch.name} آمادهٔ تحویل است.'


def _configured_sms(branch):
    try:
        config=branch.sms_provider
    except SmsProviderConfig.DoesNotExist:
        return False
    return bool(config.is_active and config.endpoint_url)


def _configured_pager(branch):
    try:
        config=branch.pager_provider
    except PagerProviderConfig.DoesNotExist:
        return False
    return bool(config.is_active and config.endpoint_url)


def _create_delivery(*, order, channel, recipient, title, body, dedupe_key, configuration_ready):
    defaults={'customer':order.customer,'recipient':recipient,'title':title,'body':body}
    if not configuration_ready:
        defaults.update(status=Notification.Status.CANCELLED,last_error='اتصال‌دهندهٔ این روش اعلان برای شعبه فعال و کامل نشده است.')
    notification,created=Notification.objects.get_or_create(
        branch=order.branch,order=order,channel=channel,event='ORDER_READY',dedupe_key=dedupe_key,defaults=defaults,
    )
    if created and configuration_ready:
        _queue_delivery(notification)
    return notification


@transaction.atomic
def enqueue_order_ready(order):
    """Queue exactly one configured fulfilment notification for a takeaway order."""
    if order.order_type!='TAKEAWAY':
        return []
    try:
        profile=order.takeaway_profile
    except Exception:
        return []

    title,customer_body=_ready_copy(order)
    created=[]
    in_app,_=Notification.objects.get_or_create(
        branch=order.branch,order=order,channel=Notification.Channel.IN_APP,event='ORDER_READY',
        dedupe_key=f'order-ready-inapp-{order.id}',
        defaults={'customer':order.customer,'title':title,'body':customer_body,'status':Notification.Status.SENT,'sent_at':timezone.now()},
    )
    created.append(in_app)

    if profile.ready_notification_method=='SMS':
        if not profile.customer_phone:
            return created
        created.append(_create_delivery(
            order=order,channel=Notification.Channel.SMS,recipient=profile.customer_phone,title=title,body=customer_body,
            dedupe_key=f'order-ready-sms-{order.id}',configuration_ready=_configured_sms(order.branch),
        ))
    elif profile.ready_notification_method=='PAGER':
        if not profile.pager_id:
            return created
        pager_body=f'سفارش #{order.order_number} آماده است.'
        created.append(_create_delivery(
            order=order,channel=Notification.Channel.PAGER,recipient=profile.pager.number,title=title,body=pager_body,
            dedupe_key=f'order-ready-pager-{order.id}',configuration_ready=_configured_pager(order.branch),
        ))
    return created


def _request_json(*, endpoint, payload, headers, timeout, allow_private=False, require_https=False):
    # SMS/pager success is defined by a 2xx response. Some providers return
    # plain text rather than JSON, so transport validation is strict while the
    # response body is intentionally ignored.
    return post_json(
        endpoint,
        payload,
        headers=headers,
        timeout=timeout,
        allow_private=allow_private,
        require_https=require_https,
        parse_response=False,
    )


def _provider_headers(config):
    headers={'Content-Type':'application/json'}
    for key,value in (config.headers or {}).items():
        headers[str(key)]=str(value).replace('{api_key}',config.api_key)
    return headers


def _provider_network_policy(branch):
    local = branch.business.deployment_type == 'LOCAL'
    return {'allow_private': local, 'require_https': not local}


def _send_sms(notification):
    try:
        config=notification.branch.sms_provider
    except SmsProviderConfig.DoesNotExist:
        raise ValueError('اتصال‌دهندهٔ پیامک تنظیم نشده است.')
    if not config.is_active or not config.endpoint_url:
        raise ValueError('اتصال‌دهندهٔ پیامک فعال نیست.')
    payload={config.phone_field:notification.recipient,config.message_field:notification.body}
    if config.sender:
        payload[config.sender_field]=config.sender
    _request_json(
        endpoint=config.endpoint_url,
        payload=payload,
        headers=_provider_headers(config),
        timeout=config.timeout_seconds,
        **_provider_network_policy(notification.branch),
    )


def _send_pager(notification):
    try:
        config=notification.branch.pager_provider
    except PagerProviderConfig.DoesNotExist:
        raise ValueError('اتصال‌دهندهٔ پیجر تنظیم نشده است.')
    if not config.is_active or not config.endpoint_url:
        raise ValueError('اتصال‌دهندهٔ پیجر فعال نیست.')
    _request_json(
        endpoint=config.endpoint_url,
        payload={config.pager_field:notification.recipient,config.message_field:notification.body},
        headers=_provider_headers(config),timeout=config.timeout_seconds,
        **_provider_network_policy(notification.branch),
    )


def _send_push(notification):
    from .models import PushProviderConfig, PushSubscription
    try:
        subscription=PushSubscription.objects.get(pk=int(notification.recipient),is_active=True)
    except (PushSubscription.DoesNotExist,ValueError):
        raise ValueError('اشتراک اعلان معتبر نیست.')
    try:
        config=notification.branch.push_provider
    except PushProviderConfig.DoesNotExist:
        raise ValueError('اتصال‌دهندهٔ اعلان مرورگر تنظیم نشده است.')
    if not config.is_active or not config.vapid_public_key or not config.get_private_key():
        raise ValueError('اتصال‌دهندهٔ اعلان مرورگر فعال نیست.')
    # Browser push endpoints are always external HTTPS services. Never let a public
    # subscription turn the worker into an internal-network request primitive.
    validate_http_target(subscription.endpoint, allow_private=False, require_https=True)
    try:
        from pywebpush import webpush
    except ImportError:
        raise ValueError('بستهٔ اعلان مرورگر نصب نشده است.')
    payload=json.dumps({'title':notification.title,'body':notification.body,'event':notification.event,'order_id':notification.order_id},ensure_ascii=False)
    try:
        webpush(subscription_info={'endpoint':subscription.endpoint,'keys':{'p256dh':subscription.p256dh,'auth':subscription.auth}},data=payload,vapid_private_key=config.get_private_key(),vapid_claims={'sub':config.subject})
    except Exception as error:
        if '410' in str(error) or '404' in str(error):
            subscription.is_active=False
            subscription.save(update_fields=['is_active','updated_at'])
        raise


@transaction.atomic
def process_notification(notification):
    # Lock only Notification itself. `order` is nullable and PostgreSQL rejects FOR UPDATE
    # on a nullable outer-joined relation.
    n=Notification.objects.select_for_update(of=('self',)).select_related('branch__business','order').get(pk=notification.pk)
    if n.status in [Notification.Status.SENT,Notification.Status.CANCELLED]:
        return n
    n.status=Notification.Status.PROCESSING
    n.attempts+=1
    n.save(update_fields=['status','attempts','updated_at'])
    try:
        if n.channel==Notification.Channel.SMS:
            _send_sms(n)
        elif n.channel==Notification.Channel.PAGER:
            _send_pager(n)
        elif n.channel==Notification.Channel.PUSH:
            _send_push(n)
        n.status=Notification.Status.SENT
        n.sent_at=timezone.now()
        n.last_error=''
        n.next_attempt_at=None
        if n.event=='ORDER_READY' and n.order_id:
            try:
                profile=n.order.takeaway_profile
                profile.notified_at=n.sent_at
                profile.save(update_fields=['notified_at','updated_at'])
            except Exception:
                pass
    except Exception:
        n.status=Notification.Status.FAILED
        n.last_error='ارسال اعلان ناموفق بود. اتصال‌دهنده و ارتباط شبکه را بررسی کنید.'
        n.next_attempt_at=timezone.now()+timedelta(minutes=min(60,2**min(n.attempts,6)))
    n.save(update_fields=['status','sent_at','last_error','next_attempt_at','updated_at'])
    return n


def process_pending(branch=None,business=None,limit=50,allow_global=False):
    queryset=Notification.objects.filter(status__in=[Notification.Status.PENDING,Notification.Status.FAILED]).filter(models.Q(next_attempt_at__isnull=True)|models.Q(next_attempt_at__lte=timezone.now())).order_by('created_at')
    if branch is not None:
        queryset=queryset.filter(branch=branch)
    elif business is not None:
        queryset=queryset.filter(branch__business=business)
    elif not allow_global:
        queryset=queryset.none()
    return [process_notification(notification) for notification in queryset[:limit]]

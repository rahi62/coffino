import ipaddress
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

from apps.businesses.models import BusinessModule
from apps.catalog.models import Product
from apps.notifications.models import SmsProviderConfig
from apps.online_ordering.models import OnlineMenuSettings
from apps.payment_gateway.models import PaymentGatewayConfig
from apps.printing.models import PrinterDevice


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _row(key, title, status, message, *, mode='configuration', details=None):
    return {
        'key': key,
        'title': title,
        'status': status,
        'message': message,
        'mode': mode,
        'details': details or {},
    }


def _module_map(branch):
    return {
        row.key: row.enabled
        for row in BusinessModule.objects.filter(business=branch.business)
    }


def _public_http_target(url, *, allow_private=False):
    parsed = urlparse(str(url or ''))
    if parsed.scheme not in ['http', 'https'] or not parsed.hostname:
        return False, 'URL معتبر HTTP/HTTPS نیست.'
    if parsed.username or parsed.password:
        return False, 'قرار دادن credential داخل URL برای Health Check مجاز نیست.'
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    except OSError:
        return False, 'نام میزبان قابل Resolve نیست.'
    for item in addresses:
        try:
            ip = ipaddress.ip_address(item[4][0])
        except ValueError:
            continue
        unsafe = ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified or ip.is_private
        if unsafe and not allow_private:
            return False, 'Health Check شبکه برای آدرس خصوصی/داخلی در استقرار سروری مسدود است.'
    return True, ''


def _safe_http_probe(url, *, timeout=5, allow_private=False):
    allowed, reason = _public_http_target(url, allow_private=allow_private)
    if not allowed:
        return False, None, reason
    request = urllib.request.Request(
        str(url),
        method='HEAD',
        headers={'User-Agent': 'Cafino-Health/1.0', 'Accept': '*/*'},
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=max(1, min(int(timeout or 5), 8))) as response:
            code = int(getattr(response, 'status', 200) or 200)
            return code < 500, code, 'Endpoint در دسترس است.' if code < 500 else 'Endpoint خطای سرور برگرداند.'
    except urllib.error.HTTPError as error:
        code = int(error.code)
        # 3xx/4xx (including 401/403/405) proves the host and HTTP service are reachable.
        return code < 500, code, 'Endpoint قابل دسترس است؛ پاسخ کاربردی نیازمند درخواست معتبر Provider است.' if code < 500 else 'Endpoint خطای سرور برگرداند.'
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, None, 'اتصال شبکه به Endpoint برقرار نشد.'


def _summary(rows):
    active = [row for row in rows if row['status'] != 'skipped']
    return {
        'ok': sum(1 for row in active if row['status'] == 'ok'),
        'warning': sum(1 for row in active if row['status'] == 'warning'),
        'error': sum(1 for row in active if row['status'] == 'error'),
        'total': len(active),
    }


def _online_health(branch, enabled):
    if not enabled:
        return _row('online_menu', 'منوی آنلاین', 'skipped', 'ماژول سفارش آنلاین غیرفعال است.', mode='application')
    try:
        settings = branch.online_menu_settings
    except OnlineMenuSettings.DoesNotExist:
        return _row('online_menu', 'منوی آنلاین', 'error', 'تنظیمات منوی آنلاین برای این شعبه ساخته نشده است.', mode='application')
    product_count = Product.objects.filter(branch=branch, is_available=True).count()
    if not settings.public_slug or not settings.public_base_url:
        return _row('online_menu', 'منوی آنلاین', 'error', 'Slug یا Public Base URL کامل نیست.', mode='application')
    if product_count == 0:
        return _row('online_menu', 'منوی آنلاین', 'error', 'هیچ محصول فعالی برای نمایش در منوی عمومی وجود ندارد.', mode='application', details={'products': 0})
    if not settings.is_enabled or not settings.accepting_orders:
        return _row('online_menu', 'منوی آنلاین', 'warning', 'منوی عمومی قابل ساخت است اما پذیرش سفارش هنوز فعال نشده است.', mode='application', details={'products': product_count, 'slug': settings.public_slug})
    return _row('online_menu', 'منوی آنلاین', 'ok', 'منوی عمومی تنظیم است و سفارش آنلاین پذیرش می‌شود.', mode='application', details={'products': product_count, 'slug': settings.public_slug})


def _sms_health(branch, enabled, *, live=False):
    if not enabled:
        return _row('sms', 'پیامک', 'skipped', 'ماژول SMS غیرفعال است.')
    try:
        config = branch.sms_provider
    except SmsProviderConfig.DoesNotExist:
        return _row('sms', 'پیامک', 'error', 'Provider پیامک برای این شعبه تعریف نشده است.')
    if not config.is_active or not config.endpoint_url:
        return _row('sms', 'پیامک', 'error', 'Provider پیامک باید فعال باشد و Endpoint داشته باشد.')
    details = {
        'provider': config.provider_name,
        'api_key_configured': bool(config.api_key_encrypted),
        'sender_configured': bool(config.sender),
    }
    if not live:
        return _row('sms', 'پیامک', 'warning', 'پیکربندی کامل است؛ برای بررسی دسترسی شبکه Live Check را اجرا کنید.', mode='configuration', details=details)
    allow_private = branch.business.deployment_type == 'LOCAL'
    ok, code, message = _safe_http_probe(config.endpoint_url, timeout=config.timeout_seconds, allow_private=allow_private)
    details['http_status'] = code
    return _row('sms', 'پیامک', 'ok' if ok else 'error', message, mode='network', details=details)


def _gateway_health(branch, enabled, *, live=False):
    try:
        menu = branch.online_menu_settings
        online_required = menu.payment_mode == OnlineMenuSettings.PaymentMode.ONLINE
    except OnlineMenuSettings.DoesNotExist:
        online_required = False
    if not enabled and not online_required:
        return _row('payment_gateway', 'درگاه پرداخت', 'skipped', 'پرداخت آنلاین برای این شعبه فعال نیست.')
    try:
        config = branch.payment_gateway
    except PaymentGatewayConfig.DoesNotExist:
        return _row('payment_gateway', 'درگاه پرداخت', 'error', 'تنظیمات درگاه پرداخت وجود ندارد.')
    if not config.is_active:
        return _row('payment_gateway', 'درگاه پرداخت', 'error', 'درگاه پرداخت غیرفعال است.')
    details = {'provider': config.provider, 'sandbox': bool(config.sandbox)}
    if not config.callback_base_url:
        return _row('payment_gateway', 'درگاه پرداخت', 'error', 'Callback Base URL تنظیم نشده است.', details=details)
    if config.provider == PaymentGatewayConfig.Provider.MOCK:
        return _row('payment_gateway', 'درگاه پرداخت', 'ok', 'درگاه Mock و Callback برای تست داخلی Cafino آماده هستند.', mode='simulation', details=details)
    if config.provider == PaymentGatewayConfig.Provider.ZARINPAL:
        try:
            merchant_ready = bool(config.get_merchant_id())
        except Exception:
            merchant_ready = False
        if not merchant_ready:
            return _row('payment_gateway', 'درگاه پرداخت', 'error', 'Merchant ID زرین‌پال تنظیم یا قابل خواندن نیست.', details=details)
        target = 'https://api.zarinpal.com/pg/v4/payment/request.json'
    else:
        if not config.request_url:
            return _row('payment_gateway', 'درگاه پرداخت', 'error', 'Request URL برای درگاه Generic تنظیم نشده است.', details=details)
        target = config.request_url
        details['api_key_configured'] = bool(config.api_key_encrypted)
    if not live:
        return _row('payment_gateway', 'درگاه پرداخت', 'warning', 'پیکربندی Provider کامل است؛ برای بررسی دسترسی شبکه Live Check را اجرا کنید.', details=details)
    allow_private = branch.business.deployment_type == 'LOCAL'
    ok, code, message = _safe_http_probe(target, timeout=config.timeout_seconds, allow_private=allow_private)
    details['http_status'] = code
    return _row('payment_gateway', 'درگاه پرداخت', 'ok' if ok else 'error', message, mode='network', details=details)


def _printer_configuration_health(branch, enabled):
    if not enabled:
        return _row('printer', 'پرینتر', 'skipped', 'ماژول چاپ غیرفعال است.', mode='hardware')
    printers = list(PrinterDevice.objects.filter(branch=branch, is_active=True).order_by('name'))
    if not printers:
        return _row('printer', 'پرینتر', 'error', 'هیچ PrinterDevice فعالی برای این شعبه تعریف نشده است.', mode='hardware')
    configured = [printer for printer in printers if printer.system_name.strip()]
    if not configured:
        return _row('printer', 'پرینتر', 'error', 'پرینتر تعریف شده اما System Name دستگاه محلی ثبت نشده است.', mode='hardware', details={'configured': len(printers)})
    return _row(
        'printer', 'پرینتر', 'warning',
        'پیکربندی ثبت شده است؛ برای تطبیق با پرینترهای واقعی سیستم، تست Local Printer را اجرا کنید.',
        mode='hardware',
        details={'configured': len(printers), 'with_system_name': len(configured)},
    )


def settings_health_payload(branch, *, live=False):
    modules = _module_map(branch)
    rows = [
        _online_health(branch, bool(modules.get('ONLINE_ORDERING'))),
        _sms_health(branch, bool(modules.get('SMS')), live=live),
        _gateway_health(branch, bool(modules.get('PAYMENT_GATEWAY')), live=live),
        _printer_configuration_health(branch, bool(modules.get('PRINTING'))),
    ]
    return {
        'branch': {'id': branch.id, 'name': branch.name},
        'live': bool(live),
        'summary': _summary(rows),
        'checks': rows,
    }


def printer_runtime_health_payload(branch, device_names):
    configured = list(PrinterDevice.objects.filter(branch=branch, is_active=True).order_by('name'))
    clean_devices = []
    for value in list(device_names or [])[:100]:
        name = str(value or '').strip()[:250]
        if name:
            clean_devices.append(name)
    normalized = {name.casefold(): name for name in clean_devices}
    expected = [printer for printer in configured if printer.system_name.strip()]
    matched = [printer for printer in expected if printer.system_name.strip().casefold() in normalized]
    missing = [printer.name for printer in expected if printer.system_name.strip().casefold() not in normalized]
    if not configured:
        status = 'error'
        message = 'هیچ PrinterDevice فعالی برای شعبه ثبت نشده است.'
    elif not expected:
        status = 'error'
        message = 'System Name هیچ پرینتری تنظیم نشده است.'
    elif len(matched) == len(expected):
        status = 'ok'
        message = 'همه پرینترهای پیکربندی‌شده روی سیستم محلی پیدا شدند.'
    elif matched:
        status = 'warning'
        message = 'بخشی از پرینترهای پیکربندی‌شده روی سیستم محلی پیدا شدند.'
    else:
        status = 'error'
        message = 'هیچ‌یک از پرینترهای پیکربندی‌شده روی سیستم محلی پیدا نشدند.'
    row = _row(
        'printer_runtime', 'پرینتر محلی', status, message, mode='hardware-runtime',
        details={'detected': len(clean_devices), 'configured': len(expected), 'matched': len(matched), 'missing': missing},
    )
    return {'branch': {'id': branch.id, 'name': branch.name}, 'check': row}

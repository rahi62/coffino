from apps.businesses.models import BusinessModule
from apps.cashier.models import CashRegister
from apps.catalog.models import Product
from apps.delivery.models import DeliveryZone
from apps.dining.models import Hall, Table
from apps.inventory.models import InventoryItem, RecipeItem
from apps.kitchen.models import PreparationStation
from apps.notifications.models import PushProviderConfig, SmsProviderConfig
from apps.online_ordering.models import OnlineMenuSettings
from apps.payment_gateway.models import PaymentGatewayConfig
from apps.printing.models import PrinterDevice


def _check(key, title, ok, detail, href, *, required=True):
    return {
        'key': key,
        'title': title,
        'status': 'done' if ok else ('missing' if required else 'warning'),
        'required': required,
        'detail': detail,
        'href': href,
    }


def _summary(checks):
    required = [row for row in checks if row['required']]
    completed = sum(1 for row in required if row['status'] == 'done')
    total = len(required)
    return {
        'score': round((completed / total) * 100) if total else 100,
        'completed': completed,
        'total': total,
        'blocking': total - completed,
    }


def settings_readiness_payload(business):
    module_rows = BusinessModule.objects.filter(business=business)
    modules = {row.key: row.enabled for row in module_rows}

    def enabled(key):
        return key == 'CORE' or bool(modules.get(key, False))

    active_branches = list(business.branches.filter(is_active=True).order_by('name'))
    business_checks = [
        _check(
            'business_profile', 'پروفایل کسب‌وکار',
            bool(business.name and business.business_type and business.deployment_type),
            'نام، نوع کسب‌وکار و مدل استقرار باید مشخص باشند.', '/settings/business'
        ),
        _check(
            'active_branch', 'حداقل یک شعبه فعال', bool(active_branches),
            'برای شروع عملیات حداقل یک شعبه فعال لازم است.', '/settings/branches'
        ),
    ]
    if enabled('MULTI_BRANCH'):
        business_checks.append(_check(
            'multi_branch', 'پیکربندی چندشعبه‌ای', len(active_branches) >= 2,
            'ماژول چندشعبه فعال است و باید حداقل دو شعبه فعال داشته باشید.', '/settings/branches'
        ))

    branch_rows = []
    for branch in active_branches:
        checks = []
        checks.append(_check(
            'branch_contact', 'اطلاعات تماس شعبه', bool(branch.phone and branch.address),
            'تلفن و آدرس برای رسید، سفارش آنلاین و ارتباط مشتری توصیه می‌شود.', '/settings/branches', required=False
        ))

        catalog_needed = any(enabled(key) for key in ('POS', 'DINE_IN', 'TAKEAWAY', 'ONLINE_ORDERING'))
        if catalog_needed:
            checks.append(_check(
                'catalog_products', 'حداقل یک محصول قابل فروش',
                Product.objects.filter(branch=branch, is_available=True).exists(),
                'برای ثبت سفارش حداقل یک محصول فعال لازم است.', '/settings/catalog'
            ))

        if enabled('POS'):
            checks.append(_check(
                'pos_register', 'صندوق فروش فعال',
                CashRegister.objects.filter(branch=branch, is_active=True).exists(),
                'ماژول POS فعال است؛ حداقل یک صندوق فروش تعریف کنید.', '/settings/branches'
            ))

        if enabled('DINE_IN'):
            has_hall = Hall.objects.filter(branch=branch).exists()
            has_table = Table.objects.filter(hall__branch=branch).exists()
            checks.append(_check(
                'dine_in_layout', 'سالن و میز', has_hall and has_table,
                'برای سرویس داخل سالن حداقل یک سالن و یک میز لازم است.', '/settings/dining'
            ))

        if enabled('KITCHEN_DISPLAY'):
            checks.append(_check(
                'kitchen_station', 'ایستگاه آماده‌سازی',
                PreparationStation.objects.filter(branch=branch, is_active=True).exists(),
                'KDS فعال است؛ حداقل یک ایستگاه آشپزخانه/بار تعریف کنید.', '/settings/catalog'
            ))

        if enabled('INVENTORY'):
            checks.append(_check(
                'inventory_items', 'مواد و اقلام انبار',
                InventoryItem.objects.filter(branch=branch, is_active=True).exists(),
                'ماژول انبار فعال است؛ حداقل یک قلم موجودی تعریف کنید.', '/settings/catalog'
            ))

        if enabled('RECIPES'):
            checks.append(_check(
                'recipes', 'رسپی محصولات',
                RecipeItem.objects.filter(product__branch=branch).exists(),
                'ماژول رسپی فعال است؛ برای محصولات آماده حداقل یک رسپی ثبت کنید.', '/settings/catalog'
            ))

        if enabled('PRINTING'):
            checks.append(_check(
                'printer', 'پرینتر فعال',
                PrinterDevice.objects.filter(branch=branch, is_active=True).exists(),
                'ماژول چاپ فعال است؛ یک پرینتر رسید یا تیکت تعریف کنید.', '/printing'
            ))

        menu = OnlineMenuSettings.objects.filter(branch=branch).first() if enabled('ONLINE_ORDERING') else None
        if enabled('ONLINE_ORDERING'):
            checks.append(_check(
                'online_config', 'تنظیمات منوی آنلاین', bool(menu),
                'تنظیمات پیش‌فرض منوی عمومی و QR را ایجاد کنید.', '/settings/online'
            ))
            checks.append(_check(
                'online_live', 'پذیرش سفارش آنلاین', bool(menu and menu.is_enabled and menu.accepting_orders),
                'منوی آنلاین ساخته شده اما برای دریافت سفارش باید فعال و در حالت پذیرش باشد.', '/settings/online', required=False
            ))

        if enabled('DELIVERY'):
            checks.append(_check(
                'delivery_zone', 'محدوده ارسال فعال',
                DeliveryZone.objects.filter(branch=branch, is_active=True).exists(),
                'ماژول ارسال فعال است؛ حداقل یک محدوده ارسال تعریف کنید.', '/settings/online'
            ))

        online_payment_required = bool(menu and menu.payment_mode == OnlineMenuSettings.PaymentMode.ONLINE)
        if enabled('PAYMENT_GATEWAY') or online_payment_required:
            gateway = PaymentGatewayConfig.objects.filter(branch=branch).first()
            checks.append(_check(
                'payment_gateway', 'درگاه پرداخت فعال', bool(gateway and gateway.is_active),
                'برای پرداخت آنلاین یک درگاه فعال لازم است.', '/settings/online'
            ))

        if enabled('SMS'):
            sms = SmsProviderConfig.objects.filter(branch=branch).first()
            checks.append(_check(
                'sms_provider', 'Provider پیامک', bool(sms and sms.is_active and sms.endpoint_url),
                'ماژول SMS فعال است؛ Endpoint و Provider فعال را تنظیم کنید.', '/settings/notifications'
            ))

        if enabled('NOTIFICATIONS'):
            push = PushProviderConfig.objects.filter(branch=branch).first()
            checks.append(_check(
                'push_provider', 'Web Push', bool(push and push.is_active and push.vapid_public_key),
                'برای اعلان مرورگر کلید VAPID بسازید و Push را فعال کنید.', '/settings/notifications', required=False
            ))

        summary = _summary(checks)
        branch_rows.append({
            'branch': branch.id,
            'name': branch.name,
            **summary,
            'checks': checks,
        })

    all_required_checks = list(business_checks)
    for row in branch_rows:
        all_required_checks.extend(row['checks'])
    overall = _summary(all_required_checks)

    return {
        'overall': overall,
        'business': {
            **_summary(business_checks),
            'checks': business_checks,
        },
        'branches': branch_rows,
        'active_modules': sorted([key for key, value in modules.items() if value] + ['CORE']),
    }

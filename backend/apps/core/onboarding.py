from django.db import transaction
from django.utils.text import slugify

from apps.audit.services import log_action
from apps.businesses.models import Branch, Business, BusinessModule
from apps.cashier.models import CashRegister
from apps.dining.models import Hall, Table
from apps.kitchen.models import PreparationStation
from apps.online_ordering.services import ensure_settings
from apps.core.settings_readiness import settings_readiness_payload


PRESETS = {
    'CAFE': {
        'label': 'کافه',
        'business_type': 'CAFE',
        'description': 'POS، سالن، بیرون‌بر، KDS، چاپ، مشتریان و گزارش‌ها برای شروع سریع یک کافه.',
        'modules': ['POS', 'DINE_IN', 'TAKEAWAY', 'KITCHEN_DISPLAY', 'PRINTING', 'CUSTOMERS', 'REPORTING'],
        'stations': ['بار قهوه', 'آشپزخانه'],
    },
    'RESTAURANT': {
        'label': 'رستوران',
        'business_type': 'RESTAURANT',
        'description': 'سالن و KDS همراه انبار، رسپی، خرید، حسابداری مدیریتی، رزرو و چاپ.',
        'modules': ['POS', 'DINE_IN', 'TAKEAWAY', 'KITCHEN_DISPLAY', 'INVENTORY', 'RECIPES', 'PURCHASING', 'ACCOUNTING', 'CUSTOMERS', 'REPORTING', 'PRINTING', 'RESERVATION'],
        'stations': ['آشپزخانه', 'بار / نوشیدنی', 'بسته‌بندی'],
    },
    'FAST_FOOD': {
        'label': 'فست‌فود',
        'business_type': 'FAST_FOOD',
        'description': 'فروش سریع، بیرون‌بر، ارسال، KDS، سفارش آنلاین، درگاه، انبار و گزارش‌ها.',
        'modules': ['POS', 'TAKEAWAY', 'KITCHEN_DISPLAY', 'INVENTORY', 'RECIPES', 'PURCHASING', 'CUSTOMERS', 'REPORTING', 'PRINTING', 'ONLINE_ORDERING', 'DELIVERY', 'PAYMENT_GATEWAY', 'NOTIFICATIONS'],
        'stations': ['آشپزخانه', 'سرخ‌کن / گریل', 'بسته‌بندی'],
    },
    'BAKERY': {
        'label': 'بیکری',
        'business_type': 'BAKERY',
        'description': 'POS، تولید Batch، رسپی، انبار، خرید، هزینه، وفاداری و گزارش حاشیه سود.',
        'modules': ['POS', 'TAKEAWAY', 'INVENTORY', 'RECIPES', 'PRODUCTION', 'PURCHASING', 'ACCOUNTING', 'CUSTOMERS', 'LOYALTY', 'REPORTING', 'PRINTING'],
        'stations': ['کانتر فروش', 'تولید'],
    },
    'PASTRY': {
        'label': 'قنادی',
        'business_type': 'PASTRY',
        'description': 'فروش، تولید، انبار، رسپی، خرید، مشتریان، وفاداری، گزارش و چاپ.',
        'modules': ['POS', 'TAKEAWAY', 'INVENTORY', 'RECIPES', 'PRODUCTION', 'PURCHASING', 'ACCOUNTING', 'CUSTOMERS', 'LOYALTY', 'REPORTING', 'PRINTING'],
        'stations': ['ویترین / فروش', 'کارگاه تولید'],
    },
    'CATERING': {
        'label': 'کترینگ',
        'business_type': 'CATERING',
        'description': 'سفارش، ارسال، تولید، خرید، انبار، رسپی، حسابداری مدیریتی و سفارش آنلاین.',
        'modules': ['POS', 'TAKEAWAY', 'KITCHEN_DISPLAY', 'INVENTORY', 'RECIPES', 'PRODUCTION', 'PURCHASING', 'ACCOUNTING', 'CUSTOMERS', 'REPORTING', 'PRINTING', 'ONLINE_ORDERING', 'DELIVERY', 'PAYMENT_GATEWAY'],
        'stations': ['آشپزخانه تولید', 'بسته‌بندی / ارسال'],
    },
    'HOTEL_RESTAURANT': {
        'label': 'رستوران هتل',
        'business_type': 'HOTEL_RESTAURANT',
        'description': 'سالن، رزرو، KDS، انبار، خرید، گزارش و قابلیت چندشعبه‌ای برای عملیات هتلی.',
        'modules': ['POS', 'DINE_IN', 'TAKEAWAY', 'KITCHEN_DISPLAY', 'INVENTORY', 'RECIPES', 'PURCHASING', 'ACCOUNTING', 'CUSTOMERS', 'REPORTING', 'PRINTING', 'RESERVATION', 'MULTI_BRANCH'],
        'stations': ['آشپزخانه', 'بار / نوشیدنی', 'روم سرویس / تحویل'],
    },
}

VALID_DEPLOYMENTS = {'LOCAL', 'SAAS', 'DEDICATED'}


def onboarding_presets_payload():
    return {
        'presets': [
            {
                'key': key,
                'label': value['label'],
                'business_type': value['business_type'],
                'description': value['description'],
                'modules': list(value['modules']),
                'stations': list(value['stations']),
            }
            for key, value in PRESETS.items()
        ]
    }


def _as_int(value, *, default=0, minimum=0, maximum=200, field='عدد'):
    if value in [None, '']:
        return default
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field} نامعتبر است')
    if result < minimum or result > maximum:
        raise ValueError(f'{field} باید بین {minimum} و {maximum} باشد')
    return result


def _station_code(name, index):
    raw = slugify(name, allow_unicode=False).replace('-', '_').upper()
    return (raw or f'STATION_{index}')[:40]


@transaction.atomic
def apply_onboarding_preset(*, business, actor, payload, request=None):
    business = Business.objects.select_for_update().get(pk=business.pk)
    preset_key = str(payload.get('preset') or '').strip().upper()
    preset = PRESETS.get(preset_key)
    if not preset:
        raise ValueError('Preset راه‌اندازی معتبر نیست')

    deployment_type = str(payload.get('deployment_type') or business.deployment_type or 'LOCAL').upper()
    if deployment_type not in VALID_DEPLOYMENTS:
        raise ValueError('مدل استقرار نامعتبر است')

    before_modules = sorted(BusinessModule.objects.filter(business=business, enabled=True).values_list('key', flat=True))
    before = {
        'business_type': business.business_type,
        'deployment_type': business.deployment_type,
        'modules': before_modules,
    }

    business.business_type = preset['business_type']
    business.deployment_type = deployment_type
    business.save(update_fields=['business_type', 'deployment_type', 'updated_at'])

    branch_id = payload.get('branch')
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.select_for_update().get(pk=branch_id, business=business)
        except Branch.DoesNotExist:
            raise ValueError('شعبه انتخاب‌شده متعلق به این کسب‌وکار نیست')
    else:
        branch = Branch.objects.select_for_update().filter(business=business, is_active=True).order_by('id').first()
        if branch is None:
            branch = Branch.objects.create(
                business=business,
                name=str(payload.get('branch_name') or 'شعبه اصلی').strip() or 'شعبه اصلی',
                address=str(payload.get('branch_address') or '').strip(),
                phone=str(payload.get('branch_phone') or '').strip(),
                is_active=True,
            )

    branch_fields = []
    if payload.get('branch_name') is not None:
        name = str(payload.get('branch_name') or '').strip()
        if name:
            branch.name = name
            branch_fields.append('name')
    if payload.get('branch_address') is not None:
        branch.address = str(payload.get('branch_address') or '').strip()
        branch_fields.append('address')
    if payload.get('branch_phone') is not None:
        branch.phone = str(payload.get('branch_phone') or '').strip()
        branch_fields.append('phone')
    if not branch.is_active:
        branch.is_active = True
        branch_fields.append('is_active')
    if branch_fields:
        branch.save(update_fields=[*sorted(set(branch_fields)), 'updated_at'])

    replace_modules = payload.get('replace_modules', True) is not False
    if replace_modules:
        BusinessModule.objects.filter(business=business).exclude(key='CORE').update(enabled=False)

    enabled_modules = []
    for module_key in preset['modules']:
        BusinessModule.objects.update_or_create(
            business=business,
            key=module_key,
            defaults={'enabled': True},
        )
        enabled_modules.append(module_key)

    created = {'register': False, 'hall': False, 'tables': 0, 'stations': 0, 'online_settings': False}

    if 'POS' in enabled_modules and payload.get('create_register', True) is not False:
        if not CashRegister.objects.filter(branch=branch, is_active=True).exists():
            CashRegister.objects.create(
                branch=branch,
                name=str(payload.get('register_name') or 'صندوق اصلی').strip() or 'صندوق اصلی',
                is_active=True,
            )
            created['register'] = True

    table_count = _as_int(payload.get('table_count'), default=0, minimum=0, maximum=200, field='تعداد میز')
    if 'DINE_IN' in enabled_modules and table_count:
        hall_name = str(payload.get('hall_name') or 'سالن اصلی').strip() or 'سالن اصلی'
        hall, was_created = Hall.objects.get_or_create(branch=branch, name=hall_name)
        created['hall'] = was_created
        capacity = _as_int(payload.get('table_capacity'), default=4, minimum=1, maximum=30, field='ظرفیت میز')
        for number in range(1, table_count + 1):
            _, table_created = Table.objects.get_or_create(
                hall=hall,
                number=str(number),
                defaults={'capacity': capacity},
            )
            if table_created:
                created['tables'] += 1

    if 'KITCHEN_DISPLAY' in enabled_modules and payload.get('create_stations', True) is not False:
        requested = payload.get('stations')
        station_names = requested if isinstance(requested, list) and requested else preset['stations']
        for index, raw_name in enumerate(station_names[:10], start=1):
            name = str(raw_name or '').strip()
            if not name:
                continue
            station = PreparationStation.objects.filter(branch=branch, name=name).order_by('id').first()
            if station:
                if not station.is_active:
                    station.is_active = True
                    station.save(update_fields=['is_active', 'updated_at'])
                continue
            PreparationStation.objects.create(
                branch=branch,
                name=name,
                code=_station_code(name, index),
                is_active=True,
            )
            created['stations'] += 1

    if 'ONLINE_ORDERING' in enabled_modules and payload.get('create_online_settings', True) is not False:
        _, existed = None, False
        try:
            branch.online_menu_settings
            existed = True
        except Exception:
            existed = False
        ensure_settings(branch)
        created['online_settings'] = not existed

    active_modules = sorted(BusinessModule.objects.filter(business=business, enabled=True).values_list('key', flat=True))
    after = {
        'preset': preset_key,
        'business_type': business.business_type,
        'deployment_type': business.deployment_type,
        'branch': branch.id,
        'modules': active_modules,
        'bootstrap': created,
    }
    log_action(
        actor=actor,
        branch=branch,
        action='ONBOARDING_PRESET_APPLIED',
        entity=business,
        description=f"Preset {preset_key} برای {branch.name} اعمال شد",
        before=before,
        after=after,
        request=request,
    )

    return {
        'preset': preset_key,
        'business': {'id': business.id, 'name': business.name, 'business_type': business.business_type, 'deployment_type': business.deployment_type},
        'branch': {'id': branch.id, 'name': branch.name, 'address': branch.address, 'phone': branch.phone},
        'enabled_modules': active_modules,
        'created': created,
        'readiness': settings_readiness_payload(business),
    }

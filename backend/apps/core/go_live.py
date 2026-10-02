from django.conf import settings
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from apps.accounts.models import User
from apps.businesses.models import BusinessModule
from apps.core.onboarding import ALL_MODULE_KEYS
from apps.core.settings_health import settings_health_payload
from apps.core.settings_readiness import settings_readiness_payload


DEPLOYMENT_PROFILES = {
    'LOCAL': {
        'key': 'LOCAL',
        'title': 'Cafino Local',
        'summary': 'نسخه ویندوزی Local First با Django و SQLite محلی؛ عملیات روزانه بدون اینترنت ادامه دارد.',
        'database': 'SQLite محلی',
        'internet_dependency': 'غیرضروری برای عملیات اصلی؛ فقط سرویس‌های بیرونی مثل SMS نیاز به اینترنت دارند.',
        'backup_strategy': 'بکاپ SQLite تأییدشده روی دیسک/USB/Network Path + Restore با Emergency Backup.',
        'capabilities': ['POS', 'KDS', 'Inventory', 'Printing', 'Pager adapters', 'Local backup/restore'],
        'environment_template': {
            'CAF_INO_ENV': 'local',
            'DJANGO_DEBUG': '0',
            'DJANGO_SECRET_KEY': '<generated-and-kept-local>',
            'DATABASE_URL': 'sqlite:///.../cafino.sqlite3',
            'DJANGO_ALLOWED_HOSTS': '127.0.0.1,localhost',
            'DJANGO_SECURE_SSL_REDIRECT': '0',
        },
    },
    'SAAS': {
        'key': 'SAAS',
        'title': 'Cafino Cloud SaaS',
        'summary': 'زیرساخت اشتراکی multi-tenant با PostgreSQL، HTTPS، سفارش آنلاین و دسترسی از راه دور.',
        'database': 'PostgreSQL managed',
        'internet_dependency': 'ضروری؛ سرویس عمومی باید از اینترنت و HTTPS در دسترس باشد.',
        'backup_strategy': 'Snapshot/managed backup دیتابیس + retention + restore drill دوره‌ای.',
        'capabilities': ['Multi-tenant', 'Online ordering', 'Online payment', 'Remote access', 'Multi-branch', 'Mobile clients'],
        'environment_template': {
            'CAF_INO_ENV': 'saas',
            'DJANGO_DEBUG': '0',
            'DJANGO_SECRET_KEY': '<strong-random-secret>',
            'DATABASE_URL': 'postgresql://<user>:<password>@<host>:5432/<database>',
            'DJANGO_ALLOWED_HOSTS': 'app.example.com',
            'CORS_ALLOWED_ORIGINS': 'https://app.example.com',
            'CSRF_TRUSTED_ORIGINS': 'https://app.example.com',
            'DJANGO_SECURE_SSL_REDIRECT': '1',
        },
    },
    'DEDICATED': {
        'key': 'DEDICATED',
        'title': 'Cafino Dedicated Managed',
        'summary': 'سرور و دیتابیس مستقل برای مشتری سازمانی با دامنه و Branding اختصاصی.',
        'database': 'PostgreSQL مستقل',
        'internet_dependency': 'ضروری برای پنل/سفارش آنلاین؛ عملیات Local فقط در صورت استقرار Hybrid جداگانه.',
        'backup_strategy': 'Backup مستقل دیتابیس + off-site copy + restore drill + مانیتورینگ Cafino.',
        'capabilities': ['Dedicated DB', 'Custom domain', 'White-label ready', 'Multi-branch', 'Managed operations'],
        'environment_template': {
            'CAF_INO_ENV': 'dedicated',
            'DJANGO_DEBUG': '0',
            'DJANGO_SECRET_KEY': '<strong-random-secret>',
            'DATABASE_URL': 'postgresql://<user>:<password>@<host>:5432/<database>',
            'DJANGO_ALLOWED_HOSTS': 'customer.example.com',
            'CORS_ALLOWED_ORIGINS': 'https://customer.example.com',
            'CSRF_TRUSTED_ORIGINS': 'https://customer.example.com',
            'DJANGO_SECURE_SSL_REDIRECT': '1',
        },
    },
}


def deployment_profiles_payload():
    return {'profiles': list(DEPLOYMENT_PROFILES.values())}


def _row(key, title, status, detail, *, category='server', blocking=None):
    if blocking is None:
        blocking = status == 'error'
    return {
        'key': key,
        'title': title,
        'status': status,
        'detail': detail,
        'category': category,
        'blocking': bool(blocking),
    }


def _is_local_host(value):
    value = str(value or '').lower()
    return value in {'localhost', '127.0.0.1', '::1'} or value.startswith('127.')


def _server_environment_checks(deployment_type):
    profile = str(deployment_type or 'LOCAL').upper()
    checks = []
    debug = bool(getattr(settings, 'DEBUG', False))
    secret = str(getattr(settings, 'SECRET_KEY', '') or '')
    environment = str(getattr(settings, 'ENVIRONMENT', '') or '').lower()
    allowed_hosts = list(getattr(settings, 'ALLOWED_HOSTS', []) or [])
    cors = list(getattr(settings, 'CORS_ALLOWED_ORIGINS', []) or [])
    vendor = connections['default'].vendor
    ssl_redirect = bool(getattr(settings, 'SECURE_SSL_REDIRECT', False))

    checks.append(_row(
        'debug_disabled', 'Debug خاموش', 'ok' if not debug else 'error',
        'DEBUG خاموش است.' if not debug else 'DJANGO_DEBUG باید در محیط تحویل 0 باشد.'
    ))
    weak_secret = not secret or secret == 'dev-secret-change-me' or len(secret) < 16
    checks.append(_row(
        'secret_key', 'Secret Key', 'ok' if not weak_secret else 'error',
        'Secret Key غیرپیش‌فرض تنظیم شده است.' if not weak_secret else 'DJANGO_SECRET_KEY امن و غیرپیش‌فرض لازم است.'
    ))

    if profile == 'LOCAL':
        checks.append(_row(
            'environment_mode', 'پروفایل Runtime', 'ok' if environment in {'local', 'production-local'} else 'warning',
            f'CAF_INO_ENV={environment or "unset"}; برای Installer نهایی مقدار local توصیه می‌شود.', blocking=False
        ))
        checks.append(_row(
            'database_engine', 'دیتابیس Local', 'ok' if vendor == 'sqlite' else 'warning',
            f'Database vendor={vendor}. نسخه Local نهایی باید SQLite محلی داشته باشد.', blocking=False
        ))
        checks.append(_row(
            'local_hosts', 'محدوده دسترسی Backend', 'ok' if allowed_hosts and all(_is_local_host(x) for x in allowed_hosts) else 'warning',
            'Backend فقط روی hostهای محلی تعریف شده است.' if allowed_hosts and all(_is_local_host(x) for x in allowed_hosts) else 'نسخه Local بهتر است فقط localhost/127.0.0.1 را مجاز کند.', blocking=False
        ))
    else:
        expected_env = {'SAAS': {'saas', 'production'}, 'DEDICATED': {'dedicated', 'production'}}.get(profile, {'production'})
        checks.append(_row(
            'environment_mode', 'پروفایل Runtime', 'ok' if environment in expected_env else 'error',
            f'CAF_INO_ENV={environment or "unset"}; مقدار مناسب برای {profile} لازم است.'
        ))
        checks.append(_row(
            'database_engine', 'PostgreSQL', 'ok' if vendor == 'postgresql' else 'error',
            f'Database vendor={vendor}. استقرار {profile} باید PostgreSQL باشد.'
        ))
        public_hosts = [x for x in allowed_hosts if x != '*' and not _is_local_host(x)]
        checks.append(_row(
            'allowed_hosts', 'Allowed Hosts عمومی', 'ok' if public_hosts and '*' not in allowed_hosts else 'error',
            'دامنه عمومی صریح تنظیم شده است.' if public_hosts and '*' not in allowed_hosts else 'DJANGO_ALLOWED_HOSTS باید دامنه واقعی و بدون wildcard داشته باشد.'
        ))
        secure_cors = [x for x in cors if str(x).startswith('https://')]
        checks.append(_row(
            'cors_https', 'CORS روی HTTPS', 'ok' if secure_cors else 'error',
            'حداقل یک Origin امن HTTPS تنظیم شده است.' if secure_cors else 'CORS_ALLOWED_ORIGINS باید Origin واقعی HTTPS داشته باشد.'
        ))
        checks.append(_row(
            'ssl_redirect', 'HTTPS Redirect', 'ok' if ssl_redirect else 'error',
            'SECURE_SSL_REDIRECT فعال است.' if ssl_redirect else 'DJANGO_SECURE_SSL_REDIRECT باید برای استقرار عمومی فعال باشد.'
        ))

    try:
        executor = MigrationExecutor(connections['default'])
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        checks.append(_row(
            'migrations', 'Migrationهای دیتابیس', 'ok' if not pending else 'error',
            'تمام migrationهای ثبت‌شده اعمال شده‌اند.' if not pending else f'{len(pending)} migration هنوز اعمال نشده است.'
        ))
    except Exception as exc:
        checks.append(_row('migrations', 'Migrationهای دیتابیس', 'warning', f'بررسی migration ممکن نشد: {exc.__class__.__name__}', blocking=False))

    return checks


def _business_checks(business):
    checks = []
    checks.append(_row(
        'business_active', 'کسب‌وکار فعال', 'ok' if business.is_active else 'error',
        'Business فعال است.' if business.is_active else 'Business غیرفعال است و نباید Go-Live شود.', category='business'
    ))
    branches = list(business.branches.filter(is_active=True).order_by('id'))
    checks.append(_row(
        'active_branch', 'حداقل یک شعبه فعال', 'ok' if branches else 'error',
        f'{len(branches)} شعبه فعال.' if branches else 'هیچ شعبه فعالی تعریف نشده است.', category='business'
    ))
    owner_exists = User.objects.filter(is_active=True, role=User.Role.OWNER).filter(
        business=business
    ).exists() or User.objects.filter(is_active=True, role=User.Role.OWNER, branch__business=business).exists()
    checks.append(_row(
        'owner_user', 'مالک فعال', 'ok' if owner_exists else 'error',
        'حداقل یک Owner فعال وجود دارد.' if owner_exists else 'قبل از تحویل باید حداقل یک Owner فعال ساخته شود.', category='business'
    ))

    explicit = set(BusinessModule.objects.filter(business=business).values_list('key', flat=True))
    missing = [key for key in ALL_MODULE_KEYS if key not in explicit]
    checks.append(_row(
        'module_state', 'State صریح ماژول‌ها', 'ok' if not missing else 'error',
        'تمام ماژول‌های شناخته‌شده state صریح دارند.' if not missing else 'Module state مبهم است: ' + ', '.join(missing), category='business'
    ))
    return checks


def _health_for_business(business):
    rows = []
    for branch in business.branches.filter(is_active=True).order_by('id'):
        payload = settings_health_payload(branch, live=False)
        for check in payload.get('checks', []):
            status = check.get('status')
            if status == 'skipped':
                continue
            rows.append({
                'branch': branch.id,
                'branch_name': branch.name,
                'key': check.get('key'),
                'title': check.get('title'),
                'status': 'error' if status == 'error' else ('warning' if status == 'warning' else 'ok'),
                'detail': check.get('message', ''),
                'category': 'integration',
                'blocking': status == 'error',
                'mode': check.get('mode', ''),
            })
    return rows


def go_live_payload(business):
    deployment = str(business.deployment_type or 'LOCAL').upper()
    profile = DEPLOYMENT_PROFILES.get(deployment, DEPLOYMENT_PROFILES['LOCAL'])
    server_checks = _server_environment_checks(deployment)
    business_checks = _business_checks(business)
    readiness = settings_readiness_payload(business)
    health = _health_for_business(business)

    readiness_blockers = int(readiness.get('overall', {}).get('blocking', 0) or 0)
    explicit_blockers = sum(1 for row in [*server_checks, *business_checks, *health] if row.get('blocking'))
    warnings = sum(1 for row in [*server_checks, *business_checks, *health] if row.get('status') == 'warning')
    blockers = explicit_blockers + readiness_blockers
    total = len(server_checks) + len(business_checks) + len(health) + int(readiness.get('overall', {}).get('total', 0) or 0)
    completed = max(total - blockers - warnings, 0)
    score = round((completed / total) * 100) if total else 100

    return {
        'business': {'id': business.id, 'name': business.name, 'deployment_type': deployment},
        'profile': profile,
        'summary': {
            'ready': blockers == 0,
            'score': score,
            'blockers': blockers,
            'warnings': warnings,
            'total': total,
        },
        'server_checks': server_checks,
        'business_checks': business_checks,
        'readiness': readiness,
        'integration_checks': health,
        'next_action': 'ready_for_delivery' if blockers == 0 else 'resolve_blockers',
    }
